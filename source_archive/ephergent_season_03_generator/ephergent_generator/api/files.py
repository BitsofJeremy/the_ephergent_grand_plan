import os
from flask import current_app, send_from_directory, request
from flask_restx import Namespace, Resource, fields, reqparse
from werkzeug.utils import secure_filename

# Create a files namespace
ns = Namespace('files', description='File management operations')

# File Model
file_model = ns.model('File', {
    'filename': fields.String(required=True, description='File name'),
    'path': fields.String(description='File path'),
    'type': fields.String(description='File type/extension'),
    'size': fields.Integer(description='File size in bytes'),
    'created_at': fields.DateTime(description='File creation timestamp')
})

# File Upload Model
file_upload_model = ns.model('FileUpload', {
    'filename': fields.String(required=True, description='Uploaded file name'),
    'path': fields.String(description='File path after upload')
})

# Create file upload parser
file_upload_parser = reqparse.RequestParser()
file_upload_parser.add_argument('file', location='files', type=str, required=True, help='File to upload')
file_upload_parser.add_argument('category', location='form', type=str, required=False, 
                                 help='Category for file upload (e.g., images, audio, video)')

@ns.route('/upload')
class FileUpload(Resource):
    @ns.expect(file_upload_parser)
    @ns.marshal_with(file_upload_model)
    def post(self):
        """Upload a file"""
        args = file_upload_parser.parse_args()
        
        # Get the file from the request
        uploaded_file = request.files['file']
        
        # Validate file
        if not uploaded_file:
            ns.abort(400, message="No file uploaded")
        
        # Secure the filename
        filename = secure_filename(uploaded_file.filename)
        
        # Determine upload category
        category = args.get('category', 'uploads')
        
        try:
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], category)
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename to prevent overwriting
            filepath = os.path.join(upload_dir, filename)
            
            # If file exists, add a timestamp
            if os.path.exists(filepath):
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(upload_dir, filename)
            
            # Save the file
            uploaded_file.save(filepath)
            
            return {
                'filename': filename,
                'path': filepath
            }, 201
        
        except Exception as e:
            current_app.logger.error(f"File upload error: {str(e)}")
            ns.abort(500, message="An error occurred while uploading the file")

@ns.route('/download/<path:filename>')
class FileDownload(Resource):
    def get(self, filename):
        """Download a file"""
        try:
            # Validate and secure filename
            secure_fn = secure_filename(filename)
            
            # Determine directory based on file type
            def find_file_directory(secure_fn):
                directories = [
                    current_app.config['UPLOAD_FOLDER'],
                    os.path.join(current_app.config['STATIC_FOLDER'], 'images'),
                    os.path.join(current_app.config['STATIC_FOLDER'], 'audio'),
                    os.path.join(current_app.config['STATIC_FOLDER'], 'video')
                ]
                
                for directory in directories:
                    filepath = os.path.join(directory, secure_fn)
                    if os.path.exists(filepath):
                        return directory
                
                return None
            
            directory = find_file_directory(secure_fn)
            
            if not directory:
                ns.abort(404, message="File not found")
            
            return send_from_directory(directory, secure_fn, as_attachment=True)
        
        except Exception as e:
            current_app.logger.error(f"File download error: {str(e)}")
            ns.abort(500, message="An error occurred while downloading the file")

@ns.route('/list')
class FileList(Resource):
    @ns.marshal_with(file_model, as_list=True)
    def get(self):
        """List files in a specified directory"""
        # Optional filter for file type/category
        category = request.args.get('category', 'uploads')
        
        try:
            # Determine directory
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], category)
            
            # List files with details
            files = []
            for filename in os.listdir(upload_dir):
                filepath = os.path.join(upload_dir, filename)
                
                # Skip directories
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    files.append({
                        'filename': filename,
                        'path': filepath,
                        'type': os.path.splitext(filename)[1],
                        'size': stat.st_size,
                        'created_at': stat.st_ctime
                    })
            
            return files, 200
        
        except Exception as e:
            current_app.logger.error(f"File listing error: {str(e)}")
            ns.abort(500, message="An error occurred while listing files")