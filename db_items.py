from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import User, Category, Item, Base

engine = create_engine('sqlite:///catalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Create dummy user
User1 = User(name="Sai Manoj", email="saimanoj58@gmail.com")
session.add(User1)
session.commit()

# Menu for Floor Tiles
category1 = Category(name="Wall Tiles", user_id="1")

session.add(category1)
session.commit()

menuItem1 = Item(name="Johnson NEO Collection",
                     description="Digital Wall Tiles(30x60cm) with recommended Floor Tiles",
                     category_id=1, user_id=1)

session.add(menuItem1)
session.commit()

menuItem2 = Item(name="Johnson Ornato",
                     description="Ceramic 3D Wall Tiles Concepts",
                     category_id=1, user_id=1)

session.add(menuItem2)
session.commit()


menuItem3 = Item(name="Johnson Natura",
                     description="Elevation Wall Tile Collection",
                     category_id=1, user_id=1)

session.add(menuItem3)
session.commit()


# Menu for Biryani Pot
category2 = Category(name="Floor Tiles", user_id="1")

session.add(category2)
session.commit()


menuItem1 = Item(name="Johnson Ceramic Stain & Scratch Resistant (SSR)",
                     description="Northen Collection - Rajkot (Available in rest of India)",
                     category_id=2, user_id=1)

session.add(menuItem1)
session.commit()

menuItem2 = Item(name="Johnson Ceramic Stain & Scratch Resistant (SSR)",
                     description="Southern Collection - Vijaywada (Available in South India only)",
                     category_id=2, user_id=1)

session.add(menuItem2)
session.commit()


print "Added menu items!"
