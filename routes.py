from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from database import mongo

upload_route = Blueprint('upload_route', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_route.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'})

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        db_entry = {
            'filename': filename,
            'file_path': file_path,
        }
        mongo.db.images.insert_one(db_entry)

        return jsonify({'message': 'File uploaded successfully'})

    return jsonify({'error': 'Invalid file format'})
