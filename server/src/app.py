from flask import Flask, request
from flask_restful import Resource, Api
from flask_cors import CORS

from os.path import exists

import pdb

UPLOAD_FOLDER = '/myfiles'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["SECRET_KEY"] = 'jv5(78$62-hr+8==+kn4%r*(9g)fubx&&i=3ewc9p*tnkt6u$h'
CORS(app, origins="*")
api = Api(app)

class UploadImage(Resource):
    def get(self):
        return {
            'status': 404,
            'message': 'Not allowed. Only POST'
        }
    def post(self):
        ret = {
            'status': 200,
            'message' : "Image uploaded successfully"
        }
        uploaded_file = None 
        if (request.files):
            uploaded_file = request.files["file"]
            if (not exists(f"../images/{uploaded_file.filename}")):
                uploaded_file.save(f"../images/{uploaded_file.filename}")
            else:
                ret = {
                    'status': 400,
                    'message' : "File already exists"
                }
        return ret

class Home(Resource):
    def get(self):
        return {
            'status':200,
            'message': 'Server up and running!'
        }

api.add_resource(Home, '/')
api.add_resource(UploadImage, '/img/')

# pdb.set_trace()