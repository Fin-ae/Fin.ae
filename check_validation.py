from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')
db = MongoClient(os.environ['MONGO_URL'])['finae']
opts = db.get_collection('policies_insurance').options()
print("Collection options:", opts)
