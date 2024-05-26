from flask import Flask
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/carquest'
mongo = PyMongo(app)

# Test database connection
with app.app_context():
    print(mongo.db.list_collection_names())  # Output the list of collections in the database
