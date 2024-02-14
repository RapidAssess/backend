from flask import Flask, request, jsonify, Response
import jwt
from pymongo import MongoClient
from gridfs import GridFS
from dotenv import load_dotenv
import os
import base64

from auth_middleware import token_required

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
SECRET_KEY = os.environ.get('SECRET_KEY') or 'this is a secret'
#print(SECRET_KEY)
app.config['SECRET_KEY'] = SECRET_KEY

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
# recomment deleting by username, since is is unique
# needs JWT implemented
@app.route('/deleteuser', methods=['POST'])
@token_required
def delete_user(current_user):
    try:
        # Request by anything
        #data = request.json
        result = collection.find_one({"_id":current_user['_id']})
        if result :
            # delete and store in result
            collection.delete_one(result)
            # return success message
            return jsonify({"msg": "User deleted successfully"})
        
        return jsonify({"msg": "User does not exist"})
    except Exception as e:
        return jsonify({'error': str(e)})

# updates name and password, returns message
# code to update username is commented out
# needs JWT implemented
@app.route('/edituser', methods=['POST'])
@token_required
def edit_user(current_user):
    try:
        # user to update
        # format: {"update":username to update, "username": ... "password": new password }
        data = request.json
        # check if user exists
        result = collection.find_one({"_id":current_user["_id"]})
        if result :
            # update
            dict = {}
            if "name" in data :
                dict["name"] = data["name"]
            # update username (commented since it should be unique and unchanged)
            #if "username" in data :
            #    dict["username"] = data["username"]
            if "password" in data :
                dict["password"] = data["password"]
            
            collection.update_one({'username':current_user["username"]},{"$set":dict})
            return jsonify({"msg": "User update successful"})
        return jsonify({"msg": "User does not exist"})
    except Exception as e:
        return jsonify({'error': str(e)})

# login by username and password
# Returns user token
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
                user["token"] = jwt.encode(
                    {"user_id": str(user["_id"])},
                    app.config["SECRET_KEY"],
                    algorithm="HS256"
                )
                return jsonify({"user_token": str(user['token']),"msg": "user logged in"})
        return jsonify({"msg":"password is incorrect"})
    except Exception as e:
        return jsonify({'error': str(e)})

# primarily for development
# user can be read by anything, returns all user information
# comment out when deployed
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
# Returns a user token
@app.route('/adduser', methods=['POST'])
def create_user():
    try:
        # Get JSON data from the request
        data = request.json

        # check if username already exists
        currentusername = collection.find_one({"username":data["username"]})
        if currentusername :
            return jsonify({"msg":"username taken"})

        # Insert the data into the "backend" collection
        collection.insert_one(data)
        user = collection.find_one(data)
        # Gen token
        user["token"] = jwt.encode(
            {"user_id": str(user["_id"])},
            app.config["SECRET_KEY"],
            algorithm="HS256"
        )

        # Return a JSON response
        return jsonify({'user_token': str(user['token']), 'msg': 'User added successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)





