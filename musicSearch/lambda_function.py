import json
import spotipy.util as util
import requests
import boto3
import math

db_client = boto3.client('dynamodb')

AUTH_URL = 'https://accounts.spotify.com/api/token'

# POST
auth_response = requests.post(AUTH_URL, {
    'grant_type': 'client_credentials',
    'client_id': 'b801cac6503f4cbdb66bc763a1deabed',
    'client_secret': '89cef187a9f3414cacc2e90d0794c402',
})

# convert the response to JSON
auth_response_data = auth_response.json()

# save the access token
access_token = auth_response_data['access_token']

spotifyheaders = {
    'Authorization': 'Bearer {token}'.format(token=access_token)
}

def search(q ,li, page, userid):    # add page functionality
    BASE_URL = 'https://api.spotify.com/v1/search?q='
    target = '+'.join(q.split(' '))
    limit = '&limit=' +str(li)
    offset = '&offset=' + str((page-1)*li)
    type = '&type=track'
    count = requests.get(BASE_URL+target+type+'&offset=0&limit=1', headers=spotifyheaders).json()['tracks']['total']
    r = requests.get(BASE_URL+target+type+offset+limit, headers=spotifyheaders).json()['tracks']['items']
    result = []
    for item in r:
        obj = {
                "musicId": item['id'],
                "musicName": item['name'],
                "artistName": item['artists'][0]['name'] if len(item['artists'])>0 else "",
                "imageUrl": item["album"]['images'][0]['url'] if item["album"] and item["album"]['images'] and len(item["album"]['images'])>0 else '',
                "musicUrl": item['preview_url'],
                "like": get_music_like(userid, item['id']) 
            }
        result.append(obj)
    return 200, count, result 

def get_music_like(uid, tid): 
    like = 0
    if uid == None:
        return like 
    response = db_client.get_item(
        Key={
            'userId': {
                'S': uid,
            },

        },
        TableName='user-like',
        AttributesToGet=['likelist']
    )
    if "Item" in response:
        tids = response["Item"]["likelist"]["S"].split(", ")
        if tid in tids:
            like = 1
    return like 

#def add_likes_Spotify(uid, token):

def lambda_handler(event, context):
    
    userId = None
    if "userId" in event["queryStringParameters"]:
        userId = event["queryStringParameters"]["userId"]
    
    query = event["queryStringParameters"]["q"]
    page = 1
    if  event["queryStringParameters"] and "page" in event["queryStringParameters"]:
        page = int(event["queryStringParameters"]["page"])
    limit = 12

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,OPTIONS,POST,PUT"
    }
    statusCode, count, music = search(query, limit, page, userId)
    count = str(int(math.ceil(int(count)/limit)))
    results = {
        "count":count, 
        "music":music,
        "message": "get search data successfully"
    }
    
    return {
        'statusCode': statusCode,
        'headers': headers,
        'body': json.dumps(results)
    }