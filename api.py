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

# any param can be passed for delete, returns only message
# needs cookie/user token implemented
# TO DO: check if user exists
@app.route('/deleteuser', methods=['POST'])
def delete_user():
    try:
        # Request by anything
        data = request.json

        # delete and store in result
        collection.delete_one(data)
        # return success message
        return jsonify({"msg": "User deleted successfully"})
    except Exception as e:
        return jsonify({'error': str(e)})

# updates by username, all params must be passed. returns message
# needs cookie/user token implemented
# TO DO: check if user exists
#        allow only some params to be passed
@app.route('/edituser', methods=['POST'])
def edit_user():
    try:
        # user to update
        # format: {"update":username to update, "username": ... "password": new password }
        data = request.json

        # update
        collection.update_one({'username':data["update"]},{"$set":{'name':data["name"], 'username':data["username"], 'password':data["password"]}})

        return jsonify({"msg": "User update successful"})
    except Exception as e:
        return jsonify({'error': str(e)})

# login by username and password
# may need to do password hashing here, but give it a try on front end
# TO DO: user token
@app.route('/login', methods=['POST'])
def login() :
    try :
        data = request.json

        # get the username to read
        user = collection.find_one({'username':data['username']})

        # if user exists
        if user :
            # password from request
            passwordtry = data['password']
            # compare to actual password
            if passwordtry == user['password'] :
                return jsonify({"user": str(user),"msg": "user logged in"})
        return jsonify({"msg":"password is incorrect"})
    except Exception as e:
        return jsonify({'error': str(e)})

# primarily for development
# user can be read by anything, returns all user information
# TO DO: check if user exists
@app.route('/readuser', methods=['GET'])
def read_user() :
    try:
        # params for user
        data = request.json

        result = collection.find_one(data)

        # return all user info
        user = str(result)

        return jsonify({"user": user, "msg": "User loaded successfully"})
    except Exception as e:
        return jsonify({'error': str(e)})

# this is basically just register 
# make sure to pass name, username, and password
# TO DO: check for duplicate username, password requirements?
@app.route('/adduser', methods=['POST'])
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





