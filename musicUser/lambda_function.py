from email.quoprimime import body_check
import json
import boto3 
import sys
import logging
import pymysql
import random


rds_host  = "musicdb.c4huidqjyq0x.us-east-1.rds.amazonaws.com"
db_username = "admin"
db_password = "6998ccbd"
db_name = "music" 

client = boto3.client('rds')

logger = logging.getLogger()
logger.setLevel(logging.INFO)
   
try:
    conn = pymysql.connect(host=rds_host, user=db_username, passwd=db_password, db=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
    logger.error(e)
    sys.exit()

logger.info("SUCCESS: Connection to RDS MySQL instance succeeded")

def login(body):
    password = body['password']
    email = body['email']
    action = """
    SELECT * FROM user WHERE password=%s AND email=%s
    """
    with conn.cursor() as cur:
        cur.execute(action,(password,email))
        response = cur.fetchone()
        if response!=None:
            return 200, {
                            "userId":response[0],
                            "message":"login successfully"
                    }
        else:
            return 400, {
                            "message":"incorrect email or password"
                    }

def signUp(body):
    username = body['username']
    password = body['password'] 
    email = body['email']
    if (len(password)<6):
        return 400, {
                            "message":"password should be at least 6 characters long"
                        } 
    action0 = "SELECT * FROM user WHERE email=%s"
    action3 = "SELECT * FROM user WHERE userid=%s"
    action1 = 'INSERT INTO user VALUES (%s, %s, %s, %s)'
    action2 = "SELECT * FROM user WHERE email=%s"

    with conn.cursor() as cur:
        id = username.lower() + str(random.randint(0, 10))
        while(True):
            cur.execute(action3, (id)) 
            response = cur.fetchall() 
            if len(response)>0:
                id = username.lower() + str(random.randint(0, 10))
            else:
                break
        cur.execute(action0, (email)) 
        response = cur.fetchone()
        print(response)
        if response!= None: 
            return 400, { 
                            "message":"email already exists"
                        }
        cur.execute(action1, (id, username, password, email))
        conn.commit()
        cur.execute(action2, (email))
        
        response = cur.fetchone()
        return 200, {
                            "userId":response[0],
                            "message":"create user successfully"
                    }

 
def updatePassword(body, userId):
    forget = body['forget']
    id = userId
    new = body['newPassword']
    if (len(new)<6):
        return 400, {
                            "message":"password should be at least 6 characters long"
                        }
    if forget:
        # assume email sent
        action = "UPDATE user SET password=%s WHERE userid=%s"
        with conn.cursor() as cur: 
            cur.execute(action, (new, id))
        conn.commit()
    else:
        old = body['oldPassword']
        action0 = "SELECT * FROM user WHERE userid=%s"
        action1 = "UPDATE user SET password=%s WHERE userid=%s"
        with conn.cursor() as cur:
            cur.execute(action0, (id))
            res = cur.fetchone()
            if res==None:  
                return 400, {
                            "message":"user does not exist"
                        }
            oldpassword = res[2] 
            if oldpassword != old: 
                return 400, {
                            "message":"incorrect password"
                        }
            cur.execute(action1, (new, id))
        conn.commit()
    return 200, {
                    "message":"update password successfully"
                }

def getIdByEmail(email):
    action = "SELECT * FROM user WHERE email=%s"
    cur = conn.cursor()
    cur.execute(action,(email))
    response = cur.fetchone()
    return 200, {
                            "userId":response[0],
                            "message":"retrieve userId successfully"
                    }

def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,OPTIONS,POST,PUT"
    }
    
    statusCode = 400
    
    if event["path"] == "/login":
        body = json.loads(event["body"])
        print(body)
        # body example:
        # {
        #     "email":"xxxx@xxx.com",
        #     "password":"xxxxxxx"
        # }
        
        # check user exist, return userId
        statusCode, results = login(body)

    elif event["path"] == "/signup":
        body = json.loads(event["body"])
        print(body)
        # body example:
        # {
        #     "username":"Joann",
        #     "password":"xxxxxxx",
        #     "email":"xxxx@xxx.com"
        # }

        # check user exist, if exist statusCode=400, give error message, 
        # else insert user database, return userId
        statusCode, results = signUp(body)

    elif event["path"].startswith("/password"):
        body = json.loads(event["body"])
        print(body)
        # body example:
        # user update password in the profile, need to check oldpassword first
        # {
        #     "newPassword":"xxxxxxx",
        #     "oldPassword":"xxxxxxx",
        #     "forget": False
        # }
        # when forgetting and user clicks the link to reset password
        # {
        #     "newPassword":"xxxxxxx",
        #     "forget": True
        # }

        userId = event["pathParameters"]["userId"]

        # update password
        statusCode, results = updatePassword(body, userId)

    elif event["path"] == "/forget":
        body = json.loads(event["body"])
        print(body)
        # body example:
        # {
        #     "email":"xxxx@xxx.com"
        # }

        # send email
        email = body["email"]
        statusCode, results = getIdByEmail(email)
        print(results['userId'])
        # send email(can use the joanndmw.com domain in SES)
        # user click the link(http://project-frontend222.s3-website-us-east-1.amazonaws.com/build/index.html#/forget)
        # may add cookie to the link, I don't know :/
        
        #statusCode, results = send_email(email) 

    return {
        "statusCode": statusCode,
        "headers": headers,
        "body": json.dumps(results)
    }
