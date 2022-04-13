import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_restful import Resource, Api
from flask_cors import CORS


from os.path import exists
from dotenv import load_dotenv
from numpy import broadcast
load_dotenv()
print(f"Check value of BASE_URL: {os.getenv('BASE_URL')}")

import pdb

# UPLOAD_FOLDER = '/myfiles'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'dcom'}

app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["SECRET_KEY"] = 'jv5(78$62-hr+8==+kn4%r*(9g)fubx&&i=3ewc9p*tnkt6u$h'

CORS(app, origins="*")
# socketio = SocketIO(app, cors_allowed_origins='*')
api = Api(app)
socketio = SocketIO(app, cors_allowed_origins='*')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://user:password@http://db:3306/db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


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
            try:
                os.mkdir(os.getenv('SRC_IMG_FOLDER_URL'))
            except:
                print(f"\Folder exists already\n")

            if (not exists(f"{os.getenv('SRC_IMG_FOLDER_URL')}{uploaded_file.filename}")):
                try:
                    uploaded_file.save(f"{os.getenv('SRC_IMG_FOLDER_URL')}{uploaded_file.filename}")
                    socketio.emit('new', 100, broadcast=True)
                    # pdb.set_trace()
                    # i=0
                except:
                    print("\nError when saving image\n")
                    ret = {
                        'status': 403,
                        'message' : "Error when saving image"
                    }
            else:
                ret = {
                    'status': 403,
                    'message' : "File already exists"
                }
        print(f"\n{ret}\n")
        return ret

class Home(Resource):
    def get(self):
        # socketio.emit('test', 120)
        return {
            'status':200,
            'message': 'Server up and running!'
        }

@socketio.on('connect')
def test_connnect():
    # print(f"\nSocket connected\n")
    pass

@socketio.on('disconnect')
def test_disconnnect():
    # print(f"\nSocket disconnected\n")
    pass

api.add_resource(Home, '/')
api.add_resource(UploadImage, '/img/')


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="5000")