from flask import Flask, request, jsonify, Response
from pymongo import MongoClient
from gridfs import GridFS
from dotenv import load_dotenv
import os
import base64
from bson.objectid import ObjectId

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

@app.route('/saveAI', methods=['POST'])
def ai_todb():
    try:
        file_path = 'pathoverlay.png'
        data = request.json  
        imageID = data.get('imageID')  # Need the original ID 

        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"})

        with open(file_path, 'rb') as image_file:
            # Get ID from the grid
            image_file_id = fs.put(image_file, filename='pathoverlay.png')

            
            result = collection.insert_one({
                'image_file_id': image_file_id,  
                'imageID': imageID  
            })

            
            return jsonify({
                "message": "AI Image uploaded successfully",
                "aiID": str(result.inserted_id),  # MongoDB  ID 
                "image_file_id": str(image_file_id),  # GridFS file ID
                "imageID": imageID
            })

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/updateAI/<string:aiID>', methods=['PUT'])
def update_ai(aiID):
    try:
        data = request.json
        result = collection.update_one(
            {"_id": ObjectId(aiID)},
            {"$set": data}  
        )

        if result.modified_count:
            return jsonify({"message": "AI Image metadata updated successfully"})
        else:
            return jsonify({"error": "No update performed"})
    except Exception as e:
        return jsonify({"error": str(e)})






@app.route('/update/<string:image_id>', methods=['PUT'])
def update_image(image_id):
    try:
        
        data = request.json

        
        result = collection.update_one(
            {"_id": ObjectId(image_id), 'ifImage': 'Yes'},
            {"$set": data}
        )

        if result.modified_count > 0:
            return jsonify({"message": "Image updated successfully"})
        else:
            return jsonify({"error": "No update performed"})

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/deleteAI/<string:aiID>', methods=['DELETE'])
def delete_aiimage(aiID):
    try:
        document = collection.find_one_and_delete({"_id": ObjectId(aiID)})
        if document:
            fs.delete(document['image_file_id'])  # Delete the image file from GridFS
            return jsonify({"message": "AI Image deleted successfully"})
        else:
            return jsonify({"error": "No update performed"})
    except Exception as e:
        return jsonify({"error": str(e)})



@app.route('/delete/<string:image_id>', methods=['DELETE'])
def delete_image(image_id):
    try:
        
        document = collection.find_one_and_delete({"_id": ObjectId(image_id)})
        if document:
            fs.delete(document['image_file_id'])
            return jsonify({"message": "Image deleted successfully"})
        else:
            return jsonify({"error": "Image not found"})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/image', methods=['POST'])
def insert_img():
    try:
        if 'image' in request.files:
            image = request.files['image']
            name = request.form.get("name", "")  # Get the name from the request
            description = request.form.get("description", "")  # Get the description from the request

            # Save the uploaded image to a file temporarily
            image_path = 'img.jpg'
            image.save(image_path)

            # GridFS file and insert to MongoDB 
            with open(image_path, 'rb') as image_file:
                image_id = fs.put(image_file, filename=image.filename, name=name, description=description)

            # Insert the image file ID into the 'backend' collection
            result = collection.insert_one({'image_file_id': image_id, 'ifImage': 'Yes', 'name': name, 'description': description})

            

            # Return the image document ID in the response
            return jsonify({"message": "Image uploaded successfully", "imageID": str(result.inserted_id)})
        else:
            return jsonify({"error": "No image file provided in the request"})

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/aiimages/<string:imageID>', methods=['GET'])
def get_images_by_imageID(imageID):
    try:
        
        metadata_docs = list(collection.find({"imageID": imageID}))
        if not metadata_docs:
            return jsonify({"error": "No images found with the provided imageID"})

        images = []
        for doc in metadata_docs:
            try:
                file_id = doc['image_file_id']
                grid_out = fs.get(file_id)
                image_data = grid_out.read()
                encoded_image = base64.b64encode(image_data).decode('utf-8')
                
                images.append({
                    "aiID": str(doc['_id']),
                    "imageID": doc['imageID'],
                    "aiData": encoded_image,  # Sending the ai image as a base64-encoded string
                    "name": doc.get("name", ""),
                    "description": doc.get("description", "")
                })
            except Exception as e:
                print(f"Error retrieving file from GridFS: {e}")
                

        return jsonify({
            "message": f"Retrieved {len(images)} images successfully",
            "images": images
        })
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/images', methods=['GET'])
def get_all_images():
    try:
        image_documents = list(collection.find({"ifImage": "Yes"}))
        image_data_list = []

        for doc in image_documents:
            image_file = fs.get(doc['image_file_id'])
            if image_file:
                image_data = image_file.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')
                image_data_list.append({
                    "imageID": str(doc['_id']),  # MongoDB-generated _id as imageID
                    "image_file_id": str(doc['image_file_id']),  # Include the GridFS file ID
                    "data": base64_data,
                    "name": doc.get("name", ""),
                    "description": doc.get("description", "")
                })

        return jsonify({"images": image_data_list})

    except Exception as e:
        return jsonify({"error": str(e)})





if __name__ == '__main__':
    app.run(debug=True)





