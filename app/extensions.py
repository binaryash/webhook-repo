from pymongo import MongoClient

# Setup MongoDB connection
client = MongoClient('mongodb://localhost:27017/')

# Define the Database and Collection
db = client['github_events']
mongo_collection = db['actions']
