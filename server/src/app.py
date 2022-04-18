import os
import pdb

from flask import Flask, request
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api
from flask_cors import CORS

# import mysql.connector as sql

from os.path import exists
from dotenv import load_dotenv
# from numpy import broadcast
load_dotenv()
print(f"Check value of BASE_URL: {os.getenv('BASE_URL')}")


# UPLOAD_FOLDER = '/myfiles'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'dcom'}

app = Flask(__name__)
app.config["SECRET_KEY"] = 'jv5(78$62-hr+8==+kn4%r*(9g)fubx&&i=3ewc9p*tnkt6u$h'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user:password@http://localhost:3306/db'

CORS(app, origins="*")
# socketio = SocketIO(app, cors_allowed_origins='*')
api = Api(app)
socketio = SocketIO(app, cors_allowed_origins='*')
db = SQLAlchemy(app)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name= db.Column(db.String(50), nullable=False)

    def __repr__(self,):
        return f'Image#{self.id}, '

# cnx = sql.connect(
#     user='user',
#     password='password',
#     host='127.0.0.1',
#     database='db'
# )
# cursor = cnx.cursor()
# cursor.execute("SELECT * FROM IMAGE")
# # pdb.set_trace()
# if (cursor.rowcount):
#     print("Results")
# else:
#     print("No results")

# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True


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