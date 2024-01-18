from flask import Flask, request, jsonify, Response
from pymongo import MongoClient
from gridfs import GridFS
from dotenv import load_dotenv
import os
import base64

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# MongoDB URI
mongo_uri = os.getenv("MONGO_URI")


# Connect to the MongoDB server
client = MongoClient(mongo_uri)

# Access the "RapidPrototype" database
db = client["RapidPrototype"]

# Access the "backend" collection within the database
collection = db["backend"]

# Initialize GridFS for file storage
fs = GridFS(db)

@app.route('/image', methods=['POST'])
def insert_img():
    try:
        if 'image' in request.files:
            image = request.files['image']

          
            image_path = 'img.jpg'
            image.save(image_path)

            
            image.seek(0)  # file pointer to the beginning of the file
            image_id = fs.put(image, filename=image.filename)

            # Insert the image file ID into MongoDB
            result = collection.insert_one({'image_file_id': image_id, 'ifImage': 'Yes'})
            return jsonify({"message": "Image uploaded successfully"})
        else:
            return jsonify({"error": "No image file provided in the request"})

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/saveAI', methods=['POST'])
def ai_todb():
    try:
        file_path = 'pathoverlay.png'

        # Check if the file exists
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"})

        with open(file_path, 'rb') as image_file:
            image_id = fs.put(image_file, filename='pathoverlay.png')
            result = collection.insert_one({'image_file_id': image_id, 'ifImage': 'Yes'})
            return jsonify({"message": "Image uploaded successfully"})

    except Exception as e:
        return jsonify({"error": str(e)})





@app.route('/allimg', methods=['GET'])
def all_img():
    try:
        
        image_documents = list(collection.find({"ifImage": "Yes"}))

        
        image_data_list = []

        
        for doc in image_documents:
            image_file = fs.get(doc['image_file_id'])
            if image_file:
               
                image_data = image_file.read()
                
                # Encode the binary data (image) as Base64 (text format)
                # for transfer in JSON responses.
                # UTF-8 string works with JSON
                base64_data = base64.b64encode(image_data).decode('utf-8')
                
                image_data_list.append(base64_data)

        
        return jsonify({"image_data": image_data_list})

    except Exception as e:
        return jsonify({"error": str(e)})



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





