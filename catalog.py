from flask import (Flask,
                   render_template,
                   request,
                   redirect,
                   jsonify,
                   url_for)
from flask import make_response, flash
from flask import session as login_session

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from functools import wraps

from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
from database_setup import Base, User, Category, Item

import httplib2
import json
import requests
import random
import string

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def login_required(f):
    '''checks if user is loggedin or not'''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You are not allowed to access there")
            return redirect('/login')
    return decorated_function


@app.route('/login')
def showLogin():
    ''' page to login'''
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Google login for user authentication
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    print data['email']
    if session.query(User).filter_by(email=data['email']).count() != 0:
        current_user = session.query(User).filter_by(email=data['email']).one()
    else:
        newUser = User(name=data['name'],
                       email=data['email'])
        session.add(newUser)
        session.commit()
        current_user = newUser

    login_session['user_id'] = current_user.id
    print current_user.id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '''"style = "width: 300px; height: 300px;border-radius: 150px;
                -webkit-border-radius:150px;-moz-border-radius: 150px;">'''
    flash("you are now logged in as %s" % login_session['username'])
    return output

    # DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/timepass')
def timepass():
    # query user
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    print '\n\ncategory:'
    categories = session.query(Category).all()
    for category in categories:
        print "\nid: " + str(category.id)
        print "name: " + category.name
        print "user_id: " + str(category.user_id)

    print '\n\nitems:'
    items = session.query(Item).all()
    for item in items:
        print "\nid: " + str(item.id)
        print "name: " + item.name
        print "category id: " + str(item.category_id)
        print "user_id: " + str(item.user_id)

    print '\n\nusers:'
    users = session.query(User).all()
    for user in users:
        print "\nid: " + str(user.id)
        print "name: " + user.name
        print "email id: " + str(user.email)

    return ""


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnects a connected user.
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']  # NOQA
    h = httplib2.Http()
    result = \
        h.request(uri=url, method='POST', body=None, headers={'content-type': 'application/x-www-form-urlencoded'})[0]  # NOQA

    print url
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("Successfully logged out")
        return redirect('/category')
        # return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/')
@app.route('/category/')
def showCategory():
    """Show all Categories

    Returns:
        on GET: page to show all catergory list
    """
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    categories = session.query(Category).all()
    return render_template('category.html', categories=categories)


@app.route('/category/new/', methods=['GET', 'POST'])
@login_required
def newCategory():
    """Add new Category

    Returns:
        on GET: page to create a category
        on POST: storing category to table
    """
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    user_id = login_session['user_id']

    if request.method == 'POST':
        newCategory = Category(name=request.form['name'], user_id=user_id)
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showCategory'))
    else:
        return render_template('category_new.html')


@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
@login_required
def editCategory(category_id):
    """Edit Category

    Returns:
        on GET: page to edit category
        on POST: store edited category
    """
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    category = session.query(Category).filter_by(id=category_id).one()

    if category.user_id != login_session['user_id']:
        flash('Category was created by another user and can only be edited by creator')  # NOQA
        return redirect(url_for('showCategory'))

    if request.method == 'POST':
        if request.form['name']:
            category.name = request.form['name']
        session.add(category)
        session.commit()
        flash('Category Successfully Updated %s' % category.name)
        return redirect(url_for('showCategory'))
    else:
        return render_template('category_edit.html', category=category)


@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteCategory(category_id):
    """Delete Category

    Returns:
        on GET: page to delete category
        on POST: delete's category from table
    """
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    category = session.query(Category).filter_by(id=category_id).one()

    if category.user_id != login_session['user_id']:
        flash('Category was created by another user and can only be deleted by creator')  # NOQA
        return redirect(url_for('showCategory'))

    if request.method == 'POST':
        session.delete(category)
        session.commit()

        flash('%s Successfully Deleted' % category.name)

        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template('category_delete.html', category=category)


@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/item/')
def showItem(category_id):
    """Show all Items

    Returns:
        on GET: page to show all items list in a category
    """
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(
        category_id=category_id).all()
    return render_template('item.html', items=items, category=category)


@app.route('/category/<int:category_id>/item/new', methods=['GET', 'POST'])
@login_required
def newItem(category_id):
    """Add new Item

    Returns:
        on GET: page to create a item
        on POST: storing item to table
    """
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    user_id = login_session['user_id']

    if request.method == 'POST':
        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       category_id=category_id,
                       user_id=user_id)
        session.add(newItem)
        session.commit()
        flash('%s Successfully Created' % (newItem.name))
        return redirect(url_for('showItem', category_id=category_id))
    else:
        return render_template('item_new.html', category_id=category_id)

    return render_template('item_new.html', category_id=category_id)


@app.route('/category/<int:category_id>/item/<int:item_id>/edit',
           methods=['GET', 'POST'])
@login_required
def editItem(category_id, item_id):
    """Edit Item

    Returns:
        on GET: page to edit category
        on POST: store edited category
    """
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    item = session.query(Item).filter_by(id=item_id).one()

    if item.user_id != login_session['user_id']:
        flash('Item was created by another user and can only be edited by creator')  # NOQA
        return redirect(url_for('showItem', category_id=category_id))

    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        session.add(item)
        session.commit()
        flash('%s Successfully Updated' % (item.name))
        return redirect(url_for('showItem', category_id=category_id))
    else:
        return render_template('item_edit.html',
                               category_id=category_id,
                               item_id=item_id,
                               item=item)


@app.route('/category/<int:category_id>/item/<int:item_id>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteItem(category_id, item_id):
    """Delete Item

    Returns:
        on GET: page to delete category
        on POST: delete's category from table
    """
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    item = session.query(Item).filter_by(id=item_id).one()

    if item.user_id != login_session['user_id']:
        flash('Item was created by another user and can only be deleted by creator')  # NOQA
        return redirect(url_for('showItem', category_id=category_id))

    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash('%s Successfully Deleted' % (item.name))
        return redirect(url_for('showItem', category_id=category_id))
    else:
        return render_template('item_delete.html',
                               category_id=category_id,
                               item=item)


@app.route('/category/JSON')
def categoriesJSON():
    """Return JSON for all the categories"""
    categorys = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categorys])


@app.route('/category/<int:category_id>/JSON')
def categoryJSON(category_id):
    """Return JSON of all the items for a category"""
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(
        category_id=category_id).all()
    return jsonify(items=[i.serialize for i in items])


@app.route('/item/JSON')
def itemsJSON():
    """Return JSON for an item"""
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    items = session.query(Item).all()
    return jsonify(items=[i.serialize for i in items])


@app.route('/category/<int:category_id>/item/<int:item_id>/JSON')
def itemJSON(category_id, item_id):
    """Return JSON for an item"""
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(item=item.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.run(host='0.0.0.0', port=5000)
