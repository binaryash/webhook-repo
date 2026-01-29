from pymongo import MongoClient

# Setup MongoDB connection
# Connects to the local Docker or System Mongo instance
client = MongoClient('mongodb://localhost:27017/')

# Define the Database and Collection
db = client['github_events']
mongo_collection = db['actions']
