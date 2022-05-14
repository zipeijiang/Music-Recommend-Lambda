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
 

def add_sid(uid, sid):   # add a row to dynamoDB user-like
    conn = pymysql.connect(host=rds_host, user=db_username, passwd=db_password, db=db_name, connect_timeout=5)
    sid = sid
    uid = uid 
    action0 = "SELECT * FROM spotifyid WHERE userid = %s"
    action1 = "INSERT INTO spotifyid VALUES (%s, %s)"
    action2 = "UPDATE spotifyid SET sid = %s WHERE userid = %s "
    cur=conn.cursor()
    cur.execute(action0, (uid))
    response = cur.fetchall() 
    if len(response)>0:
        cur.execute(action2, (sid, uid))
        conn.commit()
        cur.close()
        return 200, {
                        "message":"spotifyId updated successfully"
                    }
    else:
        cur.execute(action1, (uid, sid))
        conn.commit()
        cur.close() 
        return 200, {
                        "message":"spotifyId added successfully" 
                    }

def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,OPTIONS,POST,PUT"
    }
    
    statusCode = 400
    
    data = json.loads(event['Records'][0]['body']) 
    #body = event["body"] # for test
    uid = data['uid']
    sid = data['sid']
    print(uid)
    print(sid)
    
    # check user exist, return userId
    statusCode, results = add_sid(uid, sid) 
    
    return {
        "statusCode": statusCode,
        "headers": headers,
        "body": json.dumps(results)
    }
