from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')
db = MongoClient(os.environ['MONGO_URL'])['finae']

# Fetch current broken validator
opts = db.get_collection('policies_insurance').options()
validator = opts.get('validator', {})

if "" in validator:
    print("Found broken validator key, fixing it to $jsonSchema...")
    # Fix the key
    fixed_validator = {"$jsonSchema": validator[""]}
    
    # Update the collection with the fixed validator
    db.command("collMod", "policies_insurance", validator=fixed_validator)
    print("Validator fixed successfully!")
else:
    print("No broken validator found.")
