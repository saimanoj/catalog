# Item-Catalog
Create a Tiles Catalog app where users can add, edit, and delete different types of tiles and different models in the tiles.
## Setup and run the project
### Prerequisites
* Python 2.7
* Vagrant99
* VirtualBox

### How to Run
1. Install VirtualBox and Vagrant
2. Clone this repo
3. Unzip and place the Item Catalog folder in your Vagrant directory
4. Launch Vagrant
```
$ vagrant up 
```
5. Login to Vagrant
```
$ vagrant ssh
```
6. Change directory to `/vagrant`
```
$ cd /vagrant
```
7. Initialize the database
```
$ python database_setup.py
```
8. Populate the database with some initial data
```
$ python db_items.py
```
9. Launch application
```
$ python catalog.py
```
10. Open the browser and go to http://localhost:5000

### JSON endpoints
#### Returns JSON of all Category

```
/category/JSON
```
#### Returns JSON of specific menu item

```
/category/<int:category_id>/item/<int:item_id>/JSON
```
#### Returns JSON of menu

```
/category/<int:category_id>/JSON
```