import os
from pymongo import MongoClient

mongo_uri = os.getenv("MONGO_URI", "mongodb://mongo:27017/UniQDB")
client = MongoClient(mongo_uri)
db = client["UniQDB"]