
import os
from pymongo import MongoClient

# MongoDB setup
connection_string = os.getenv("MONGO_URI", "mongodb+srv://book_db:book_db@grow-cohort6.safmckr.mongodb.net/")
# print(f"Connecting to MongoDB using connection string: {connection_string}")
client = MongoClient(connection_string, serverSelectionTimeoutMS=60000)
db = client["book_db"]
collection = db["book_db"]
collection_name = db["reading_list"]

# SEARCH_QUERY = "python programming"  # Change this to your topic
# MAX_RESULTS = 10