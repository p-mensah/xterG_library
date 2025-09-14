
import os
from pymongo import MongoClient

# MongoDB setup
client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=60000)
db = client["book_db"]
collection = db["book_db"]

