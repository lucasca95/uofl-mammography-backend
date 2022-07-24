import os
import pdb
from time import sleep

from flask import Flask, redirect, request, send_file, url_for, send_file
from flask_socketio import SocketIO
from flask_restful import Resource, Api
from flask_cors import CORS
from flask_mail import Mail, Message
import jwt
import datetime
import bcrypt as bb

import pymysql
from itsdangerous import URLSafeTimedSerializer, SignatureExpired

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
# app.config["SERVER_NAME"] = 'add server name'
app.config["MAIL_SERVER"] = 'smtp.mail.yahoo.com'
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

CORS(app, origins="*")
api = Api(app)
socketio = SocketIO(app, cors_allowed_origins='*')
mail = Mail(app)
url_sts = URLSafeTimedSerializer(app.config["SECRET_KEY"])


# =============================================================================
#   Connection with DB
# =============================================================================
db_connected = False
while (not db_connected):
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='PASSWORD',
            database='lab',
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
    def post(self):
        ret = {
            'status': 200,
            'message' : "Image uploaded successfully",
            'code': -1
        }
        uploaded_file = None
        user_email = None
        if (request.files):
            uploaded_file = request.files["file"]
            try:
                os.mkdir(os.getenv('SRC_IMG_FOLDER_URL'))
            except:
                print(f"\Folder exists already\n")

            if (not exists(f"{os.getenv('SRC_IMG_FOLDER_URL')}{uploaded_file.filename}")):
                try:
                    user_email = request.values.get('email')
                    with connection.cursor() as cursor:
                        sql = """INSERT INTO IMAGE(name, user_id)VALUES(
                            %s,
                            (SELECT u.id
                            FROM APPUSER as u
                            WHERE u.email=%s)
                        )
                        """
                        cursor.execute(sql, [uploaded_file.filename, user_email])
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

                except Exception as e:
                    print(f"\nError when saving image\n{e}\n")
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

class RetrieveImageList(Resource):
    def post(self):
        print('POST -- RetrieveImageList')
        
        images = []
        user_email = request.values.get('user_email')
        try:
            with connection.cursor() as cursor:
                sql = """SELECT ii.id, 
                    ii.name, 
                    ii.detection,
                    ii.prediction_level,
                    ii.pathology,
                    ii.birads_score,
                    ii.shape
                    FROM IMAGE as ii, APPUSER as u
                    WHERE u.id = ii.user_id and u.email = %s
                """
                cursor.execute(sql, [user_email])
                for elem in cursor:
                    images.append({
                            'id': elem['id'],
                            'name': elem['name'],
                            'detection': f"{elem['detection']:0.2f}" if elem['detection'] else None,
                            'predictionLevel': elem['prediction_level'],
                            'pathology': elem['pathology'],
                            'biradsScore': elem['birads_score'],
                            'shape': elem['shape']
                        })
                    
                    
            connection.commit()
            return {
                'status': 200,
                'images': images
            }
        except Exception as e:
            print(f"\nError\n{e}\n")
            return {
                'status': 400,
                'message': 'An error has occurred'
            }

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
        return send_file(f'{os.getenv("CRON_IMG_URL")}{res["id"]}_{res["name"]}', as_attachment=False)

class RetrieveImageResults(Resource):
    def post(self):
        imgcode = request.form['imgcode']
        res = None


        # Look for image in db
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
                'message': 'Error when requesting image information'
            }
        
        # if exists...
        # # find it on server and send to frontend
        user_file = f"{res['id']}_{res['name']}"

        # We use the 'shape' field to know all the information is ready to be given to the user
        # as it is the last filed to be completed in the process.
        if ((res['shape'])):
            return {
                'status': 200,
                'prediction': res['prediction_level'],
                'detection': float(res['detection']),
                'pathology': res['pathology'],
                'birads_score': res['birads_score'],
                'shape': res['shape'],
            }
        else:
            return {
                'status': 409,
                'prediction': None,
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

class EmailConfirmation(Resource):
    def post(self):
        token = request.values.get('token')
        email = request.values.get('email')
        valid_time_window = 60*5 # seconds

        try:
            uemail = url_sts.loads(token, salt='UofLEmailToken', max_age=valid_time_window)

            with connection.cursor() as cursor:
                sql = """
                    UPDATE APPUSER as au
                    SET au.is_verified = 1
                    WHERE au.email = %s
                    """
                cursor.execute(sql, [str(email)])
            connection.commit()

            return {
                'status': 200,
                'message': "Token validated!"
            }
        except Exception as ee:
            print(f"\n{ee}\n")
            # pdb.set_trace();print('')
            email_token = url_sts.dumps(email, salt='UofLEmailToken')
            msg = Message(
                subject='Confirm your email',
                sender=app.config.get("MAIL_USERNAME"),
                recipients=[
                    email
                ],
                html=f"""
                    <h1>Email confirmation link</h1>
                    <p>Please, click <a href="http://localhost:3000/verifyemail/{email_token}/{email}">HERE</a> to confirm your email address.</p>
                """
            )
            mail.send(msg)
            return {
                'status': 201,
                'message': "Confirmation link is no longer valid. Another email will be sent with a new token."
            }
        
class RegisterClient(Resource):
    def post(self):
        try:
            ufn = request.values.get('userFirstName')
            uln = request.values.get('userLastName')
            uemail = request.values.get('userEmail')
            upass = request.values.get('userPassword')
            upasshash = bb.hashpw(upass.encode("utf-8"), bb.gensalt())
            email_token = url_sts.dumps(uemail, salt='UofLEmailToken')
            # print(f"\n\n\n{email_token}\n\n")
            
            msg = Message(
                subject='Confirm your email',
                sender=app.config.get("MAIL_USERNAME"),
                recipients=[
                    uemail
                ],
                html=f"""
                    <h1>Email confirmation link</h1>
                    <p>Please, click <a href="http://localhost:3000/verifyemail/{email_token}/{uemail}">HERE</a> to confirm your email address.</p>
                """
            )
            mail.send(msg)
            
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
                cursor.execute(sql, [ufn, uln, uemail, upasshash])
            connection.commit()

            return {
                'status': 200,
                'message': 'You have been registered successfully'
            }
        except Exception as ex:
            print(f"\n\n{str(ex)}")
            sleep(1)
            msg = 'Error when registering.'
            code = int(str(ex).split(',')[0].split('(')[1])
            if (code == 1062):
                msg += " User email has already been used."
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
                    WHERE APPUSER.email = (%s) AND is_verified = 1
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


api.add_resource(RetrieveImageList, '/images/')
api.add_resource(EmailConfirmation, '/verifyemail/')
api.add_resource(UploadImage, '/img/')
api.add_resource(RetrieveImage, '/img/retrieve/')
api.add_resource(RetrieveImageResults, '/img/retrieveresults/')
api.add_resource(Login, '/login/')
api.add_resource(RegisterClient, '/register/')
api.add_resource(Home, '/')

# =============================================================================
#   Used to run flask server as python script
# =============================================================================
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="5000")