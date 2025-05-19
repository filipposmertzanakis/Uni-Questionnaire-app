import os
import json
from pymongo import MongoClient

mongo_uri = os.getenv("MONGO_URI", "mongodb://mongo:27017/UniQDB")
client = MongoClient(mongo_uri)
db = client.get_database()

# Τσεκ εαν ειναι ηδη populated το db
if db.Students.count_documents({}) > 0:
    print("DB already has data, skipping preload.")
    exit()

# function που φορτωνει json
def load_json(filename):
    with open(filename, encoding='utf-8') as f:
        return json.load(f)

# βαζω τους students
students = load_json("students.json")
db.Students.insert_many(students)

# βαζω τα questionnaires
questionnaires = load_json("questionnaires.json")
db.Questionnaires.insert_many(questionnaires)

# βαζω τις απαντησεις
answers = load_json("answered_questionnaires.json")
db.answered_questionnaires.insert_many(answers)



print(" Database successfully preloaded.")
