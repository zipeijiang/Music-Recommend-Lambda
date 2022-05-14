import json
import spotipy.util as util
import requests
import boto3
import base64
import pymysql

db_client = boto3.client('dynamodb')

AUTH_URL = 'https://accounts.spotify.com/api/token'

# POST
auth_response = requests.post(AUTH_URL, {
    'grant_type': 'client_credentials',
    'client_id': 'ab9e1685ad7449c488cc0434e557f9a6',
    'client_secret': '78653038323d46198fa34a3db3aff5f3',
})

# convert the response to JSON
auth_response_data = auth_response.json()

# save the access token
access_token = auth_response_data['access_token']

def getHeader(accessToken):
    spotifyheaders = {
        'Authorization': 'Bearer {token}'.format(token=accessToken)
    }
    return spotifyheaders

def getPlaylists(spotifyheaders):    # add page functionality
    URL = 'https://api.spotify.com/v1/me/playlists' 
    r = requests.get(URL, headers=spotifyheaders).json()['items']
    print(r)
    result = [x['id'] for x in r]
    return result

def getMusicIds(playlists, spotifyheaders):
    musics = set()
    for id in playlists:
        URL = 'https://api.spotify.com/v1/playlists/' + id
        r = requests.get(URL, headers=spotifyheaders).json()['tracks']['items']
        mids = [item["track"]["id"] for item in r]
        musics.update(mids)
    return musics
    
def getSpotifyId(spotifyheaders):
    URL = 'https://api.spotify.com/v1/me'  
    id = requests.get(URL, headers=spotifyheaders).json()['id']
    return id

def addSid(uid, sid):
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName='playList_to_SID')
    body = json.dumps({"type":"add","uid":uid, "sid":sid})
    response = queue.send_message(MessageBody=body)
    
def updateLikes(uid, musics):
    response = db_client.get_item(
        Key={
            'userId': {
                'S': uid,
            },

        },
        TableName='user-like',
        AttributesToGet=['likelist']
    )
    if "Item" not in response:
        old = []
    else:
        old = response["Item"]["likelist"]["S"].replace(', ', ',').split(",") 
        if "" in old:
            old.remove("")
    musics.update(old)
    response = db_client.put_item(
    TableName='user-like',
    Item={
        'userId': {
            'S': uid,
        }, 
        'likelist':{
            'S': ','.join(musics),
        }
    }
    )
    return 200, {
        "message": "playlists saved successfully"
    }
        

def checkUpdate(uid):
    response = db_client.get_item(
        Key={
            'userId': {
                'S': uid,
            },

        },
        TableName='user-like',
        AttributesToGet=['likelist']
    )
    if "Item" not in response:
        old = []
    else:
        old = response["Item"]["likelist"]["S"].replace(', ', ',').split(",") 
        if "" in old:
            old.remove("")
    return old

def lambda_handler(event, context):
    userId = None
    """
    if "pathParameters" in event and "userId" in event["pathParameters"]:
        userId = event["pathParameters"]["userId"]
    """
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,OPTIONS,POST,PUT"
    }
    input = json.loads(event['body'])
    print(input) 
    #input = event['body']  
    token = input["accessToken"]  
    userId = input["userId"]   
    
    #sid = getSid(userId)  
    
    #print(sid) 
    
    spotifyheaders = getHeader(token)
    
    musics = getMusicIds(getPlaylists(spotifyheaders), spotifyheaders)
    sid = getSpotifyId(spotifyheaders)
    addSid(userId, sid) 
    statusCode, results = updateLikes(userId, musics) 
    #print(musics)  
    #print(checkUpdate(userId))
    return { 
        'statusCode': statusCode,
        'headers': headers,
        'body': json.dumps(results)
    }