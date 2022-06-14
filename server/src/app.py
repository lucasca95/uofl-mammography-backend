from crypt import methods
import os
import pdb
from time import sleep

from flask import Flask, jsonify, make_response, request, send_file
from flask_socketio import SocketIO
from flask_restful import Resource, Api
from flask_cors import CORS
from flask_mail import Mail, Message
import jwt
import datetime
import bcrypt as bb

import pymysql 
# import mysql.connector as sql

from os.path import exists
from dotenv import load_dotenv
load_dotenv()

# =============================================================================
#   Used to check the BASE_URL of the project
# =============================================================================
print(f"\nCheck value of BASE_URL: {os.getenv('BASE_URL')}\n")

# =============================================================================
#   List of allowed file extensions
# =============================================================================
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'dcom'}

# =============================================================================
#   Flask app declaration and config setup
# =============================================================================
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
mail = Mail(app)

# =============================================================================
#   Connection with DB
# =============================================================================
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
    except:
        print(f'\nError with db connection\n')
        sleep(5)

# =============================================================================
#   Route behaviors
# =============================================================================
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
            # pdb.set_trace()
            try:
                os.mkdir(os.getenv('SRC_IMG_FOLDER_URL'))
            except:
                print(f"\Folder exists already\n")

            if (not exists(f"{os.getenv('SRC_IMG_FOLDER_URL')}{uploaded_file.filename}")):
                try:
                    with connection.cursor() as cursor:
                        sql = """INSERT INTO IMAGE(name, email)VALUES(%s, %s)"""
                        cursor.execute(sql, [uploaded_file.filename, request.values.get('email')])
                        ret['code'] = cursor.lastrowid
                    connection.commit()

                    uploaded_file.save(f"{os.getenv('SRC_IMG_FOLDER_URL')}{str(ret['code'])}_{uploaded_file.filename}")
                    
                    socketio.emit('new', 100, broadcast=True)
                    
                    msg = Message(subject='Submission confirmation',
                        sender=app.config.get("MAIL_USERNAME"),
                        recipients=[
                            'lucas.camino@louisville.edu',
                            request.values.get('email')
                            # 'sahar.sinenemehdoui@louisville.edu',
                        ],
                        html="""
                            <h1>Image accepted</h1>
                            <p>Your image has been accepted for processing. Your <i>request code</i> is <strong>""" + str(ret['code']) +
                            """</strong>.</p>""")
                    mail.send(msg)

                    # pdb.set_tracle()
                    # i=0
                except Exception as e:
                    # pdb.set_trace()
                    print("\nError when saving image\n")
                    print(e)
                    if (ret['code'] != -1):
                        with connection.cursor() as cursor:
                            sql = """DELETE FROM IMAGE WHERE id=%s"""
                            cursor.execute(sql, [str(ret['code'])])
                            ret['code'] = cursor.lastrowid
                        connection.commit()
                    ret = {
                        'status': 403,
                        'message' : "Error when saving image"
                    }
            else:
                ret = {
                    'status': 403,
                    'message' : "File already exists"
                }

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
        # pdb.set_trace()
        # print('asd')
        if ((res['shape'])):
            return {
                'status': 200,
                'preduction': res['prediction_level'],
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
        return {
            'status':200,
            'message': 'Server up and running!'
        }

class RegisterClient(Resource):
    def post(self):
        try:
            ufn = request.values.get('userFirstName')
            uln = request.values.get('userLastName')
            uemail = request.values.get('userEmail')
            upass = request.values.get('userPassword')
            upasshash = bb.hashpw(upass.encode("utf-8"), bb.gensalt())
            aux = None
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO APPUSER(
                        first_name,
                        last_name,
                        email,
                        password
                    ) VALUES (
                        (%s),
                        (%s),
                        (%s),
                        (%s)
                    )
                    """
                aux = cursor.execute(sql, [ufn, uln, uemail, upasshash])
            connection.commit()
            # pdb.set_trace(); print()
            return {
                'status': 200,
                'message': 'You have been registered successfully'
            }
        except Exception as e:
            print(f"\n\n{str(e)}")
            msg = 'Error when registering.'
            code = int(str(e).split(',')[0].split('(')[1])
            if (code == 1062):
                msg += " User email has already been used."
            # pdb.set_trace()
            return {
                'status': 400,
                'message': msg
            }


class Login(Resource):
    def post(self):
        try:
            uemail = request.values.get('userEmail')
            upass = request.values.get('userPassword')

            res = None
            with connection.cursor() as cursor:
                sql = """
                    SELECT APPUSER.first_name, 
                            APPUSER.last_name, 
                            APPUSER.email, 
                            APPUSER.password
                    FROM APPUSER
                    WHERE APPUSER.email = (%s)
                    """
                cursor.execute(sql, [uemail])
                res = cursor.fetchone()
            connection.commit()
            if (res):
                # Tengo usuario. Ahora compruebo password
                if (bb.checkpw(upass.encode('utf-8'), res['password'].encode('utf-8'))):
                    # email and password match
                    token = jwt.encode({
                        'user': uemail,
                        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
                    }, app.config['SECRET_KEY'])
                    return {
                        'status': 200,
                        'message': 'Login successful',
                        'token': token
                    }

            return {
                'status': 402,
                'message': 'Credentials are not valid'
            }
        except Exception as e:
            print(f'\n{e}')
            return {
                'status': 400,
                'message': 'There has been an error'
            }

# =============================================================================
#   Functions used to test SocketIO
# =============================================================================
@socketio.on('connect')
def test_connnect():
    # print(f"\nSocket connected\n")
    pass

@socketio.on('disconnect')
def test_disconnnect():
    # print(f"\nSocket disconnected\n")
    pass

# =============================================================================
#   Routes declaration
# =============================================================================
api.add_resource(UploadImage, '/img/')
api.add_resource(RetrieveImage, '/img/retrieve/')
api.add_resource(RetrieveImageResults, '/img/retrieveresults/')
api.add_resource(Login, '/login/')
api.add_resource(RegisterClient, '/register/')
api.add_resource(Home, '/')

# @app.route('/login/', methods=['POST'])
# def login():
#     # pdb.set_trace()
#     auth = request.authorization
#     print(request.authorization)
#     if auth and auth.password == 'password':
#         token = jwt.encode({
#             'user': auth.username,
#             'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
#         }, app.config['SECRET_KEY'])
#         return jsonify({'token': token.decode('UTF-8')})
#     return make_response('Could NOT verify user', 401, {'WWW_Authenticate':'Basic realm="Login Required"'})

# =============================================================================
#   Used to run flask server as python script
# =============================================================================
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="5000")