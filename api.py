from flask import Flask, jsonify
from pymongo import MongoClient
from flask import Flask, request, jsonify
import pymongo
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the MONGO_URI variable




app = Flask(__name__)

# MongoDB URI
mongo_uri = os.getenv("MONGO_URI")
print("MONGO_URI:", mongo_uri)

# Connect to the MongoDB server
client = MongoClient(mongo_uri)

# Access the "RapidPrototype" database
db = client["RapidPrototype"]

# Access the "backend" collection within the database
collection = db["backend"]

app = Flask(__name__)

@app.route('/users', methods=['POST'])
def create_user():
    try:
        # Get JSON data from the request
        data = request.json

        # Insert the data into the "backend" collection
        result = collection.insert_one(data)

        # Get the inserted user's ID
        new_user_id = str(result.inserted_id)

        # Return a JSON response
        return jsonify({'id': new_user_id, 'msg': 'User added successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)