import os
import pdb
from time import sleep

from flask import Flask, request, send_file
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api
from flask_cors import CORS
from flask_mail import Mail, Message

import pymysql 
# import mysql.connector as sql

from os.path import exists
from dotenv import load_dotenv
# from numpy import broadcast
load_dotenv()
# print(f"Check value of BASE_URL: {os.getenv('BASE_URL')}")


# UPLOAD_FOLDER = '/myfiles'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'dcom'}

app = Flask(__name__)
app.config["SECRET_KEY"] = 'jv5(78$62-hr+8==+kn4%r*(9g)fubx&&i=3ewc9p*tnkt6u$h'
app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

CORS(app, origins="*")
api = Api(app)
socketio = SocketIO(app, cors_allowed_origins='*')



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


mail = Mail(app)

db_connected = False
while (not db_connected):
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='password',
            database='db',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        db_connected=True
        sleep(2)
    except:
        print(f'\nError with db connection\n')

# try:
#     cursor = cnx.cursor()
#     q = ("INSERT INTO IMAGE "
#         "(name) "
#         "VALUES (%s)")
#     d = (['test.png'])
#     cursor.execute(q, d)
#     i_n = cursor.lastrowid
#     print(f'{i_n}')

# except sql.Error as err:
#     print(f'\nSomething went wrong\n{err}\n')

# try:
#     cursor = cnx.cursor()
#     q = ("SELECT * "
#         "FROM IMAGE ")
#     cursor.execute(q)
#     for r in cursor:
#         print(f'{r}')

# except sql.Error as err:
#     print(f'\nSomething went wrong\n{err}\n')


# if (cursor.rowcount):
#     print("There are results")
# else:
#     print("There are no results")

class UploadImage(Resource):
    def get(self):
        return {
            'status': 404,
            'message': 'Not allowed. Only POST'
        }
    def post(self):
        ret = {
            'status': 200,
            'message' : "Image uploaded successfully",
            'code': -1
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
                    with connection.cursor() as cursor:
                        sql = """INSERT INTO IMAGE(name)VALUES(%s)"""
                        cursor.execute(sql, [uploaded_file.filename])
                        ret['code'] = cursor.lastrowid
                    connection.commit()

                    socketio.emit('new', 100, broadcast=True)

                    msg = Message(subject='Testing email',
                        sender=app.config.get("MAIL_USERNAME"),
                        recipients=[
                            'lucas.camino@louisville.edu',
                            # 'sahar.sinenemehdoui@louisville.edu',
                        ],
                        body="""This is a test email sent by the mammography backend server.""")
                    mail.send(msg)

                    # pdb.set_trace()
                    # i=0
                except Exception as e:
                    pdb.set_trace()
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
        print(f"\n\n\n{ret}\n\n\n")
        return ret

class RetrieveImage(Resource):
    def post(self):
        ret = {
            'status': 403,
            'message' : "Image not found",
            'code': -1,
        }
        imgcode = request.form['imgcode']
        res = None
        # buscar en db
        with connection.cursor() as cursor:
            sql = """
                SELECT * FROM IMAGE
                WHERE IMAGE.id = %s
                """
            cursor.execute(sql, [imgcode])
            res = cursor.fetchone()
        connection.commit()

        # if NOT exists...
        if (not res):
            print(f"\nRequested id does not exist\n")
            return {}
        
        # if exists...
        # # find it on server and send to frontend
        return send_file(f'{os.getenv("CRON_IMG_URL")+res["name"]}')

class RetrieveImageResults(Resource):
    def post(self):
        imgcode = request.form['imgcode']
        res = None
        # buscar en db
        with connection.cursor() as cursor:
            sql = """
                SELECT * FROM IMAGE
                WHERE IMAGE.id = %s
                """
            cursor.execute(sql, [imgcode])
            res = cursor.fetchone()
        connection.commit()

        # if NOT exists...
        if (not res):
            print(f"\nRequested id does not exist\n")
            return {
                'status': 404,
                'detection': -1,
                'classification': -1,
            }
        
        # if exists...
        # # find it on server and send to frontend
        pdb.set_trace()
        print('asd')
        if ((res['detection']) and (res['pathology'])
            and res['birads_score'] and res['shape']):
            return {
                'status': 200,
                'detection': float(res['detection']),
                'pathology': res['pathology'],
                'birads_score': res['birads_score'],
                'shape': res['shape'],
            }
        else:
            return {
                'status': 404,
                'detection': None,
                'pathology': None,
                'birads_score': None,
                'shape': None,
            }


class Home(Resource):
    def get(self):
        # socketio.emit('test', 120)
        # msg = Message(subject='Testing email',
        #     sender=app.config.get("MAIL_USERNAME"),
        #     recipients=[
        #         'lucas.camino@louisville.edu',
        #         'sahar.sinenemehdoui@louisville.edu',
        #     ],
        #     body="""This is a test email sent by the mammography backend server.""")
        # mail.send(msg)
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

api.add_resource(UploadImage, '/img/')
api.add_resource(RetrieveImage, '/img/retrieve/')
api.add_resource(RetrieveImageResults, '/img/retrieveresults/')
api.add_resource(Home, '/')


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="5000")