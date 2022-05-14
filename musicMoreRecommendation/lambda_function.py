import boto3
import json
import os
import random
import base64
import requests

s3_client = boto3.client('s3')
db_client = boto3.client('dynamodb')

idx2tid_data = (s3_client.get_object(Bucket='model-data-proj', Key='idx2tid.json')['Body']).read().decode('utf-8')
idx2tid = json.loads(idx2tid_data)

TOTAL_TRACK = int(os.environ['total_track']) # 22480
client_creds = os.environ['client_creds'] # <clientid:clientsecret> from Spotify Application

def get_token():
    client_creds_64 = base64.b64encode(client_creds.encode())
    token_data = {
        'grant_type': 'client_credentials'
    }
    headers = {
        'Authorization': f'Basic {client_creds_64.decode()}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    res = requests.post('https://accounts.spotify.com/api/token', data=token_data, headers=headers).json()
    return res['access_token']

def get_user_like(userId):
    response = db_client.get_item(
        Key={
            'userId': {
                'S': userId,
            },

        },
        TableName='user-like',
        AttributesToGet=['likelist']
    )
    res = []
    if "Item" in response:
        res = response["Item"]["likelist"]["S"].replace(" ", "").split(",")
    return res

def parse_query(query, like_tids):
    seed_track = ""
    if len(like_tids) > 2:
        tid_list = random.sample(like_tids, 2)
        seed_track = ",".join(tid_list)
    else:
        seed_track = ",".join(like_tids)
    if len(seed_track) == 0:
        candidates = random.sample(range(TOTAL_TRACK), 2)
        seed_track = ",".join([idx2tid[str(idx)] for idx in candidates])
        
    params = {
        "seed_artists": "4NHQUGzhtTLFvgF5SZesLK",
        "seed_genres": "classical,country",
        "seed_tracks": seed_track
    }
    for q in query:
        field, value = q.split("=")
        params[field] = value
    return params

def get_rec(params):
    api_key = get_token()
    url = "https://api.spotify.com/v1/recommendations"
    url_params = params
    headers = {
        'Authorization': 'Bearer %s' % api_key,
        'Accept': 'applicatioin/json',
        'Content-Type': 'application/json'
    }
    print(url_params["seed_tracks"]) 

    response = requests.request('GET', url, headers=headers, params=url_params)
    print(response)
    return response.json()["tracks"]

def parse_result(tracks, like_tids):
    res = []
    for track in tracks:
        musicUrl = track["preview_url"]
        if musicUrl is not None:
            tid = track["id"]
            if len(track["album"]["images"]) >= 0:
                imageUrl = track["album"]["images"][0]["url"]
            else:
                imageUrl = "https://scontent.fewr1-5.fna.fbcdn.net/v/t1.18169-1/17884567_10154570340077496_8996447567747887405_n.png?stp=dst-png_p148x148&_nc_cat=1&ccb=1-6&_nc_sid=1eb0c7&_nc_ohc=sb6jRnk6Ep4AX9IemqY&_nc_ht=scontent.fewr1-5.fna&oh=00_AT91ys0sCigXG90rAF2_y0PYp8CPc7wRuuokXyl71zEVDQ&oe=6298BB11"
            item = {
                "musicId": tid,
                "musicName": track["name"],
                "artistName" : track["artists"][0]["name"],
                "imageUrl" : imageUrl,
                "musicUrl": musicUrl,
                "like": 1 if tid in like_tids else 0
            }
            res.append(item)
    return res

def lambda_handler(event, context):
    userId = ""
    if "userId" in event["queryStringParameters"]:
        userId = event["queryStringParameters"]["userId"]
    
    like_tids = []
    if userId != "":
        like_tids = get_user_like(userId)
    
    query = event["queryStringParameters"]["q"]
    query = query.replace(" ", "").split(",")
    params = parse_query(query, like_tids)
    res = get_rec(params)
    musics = parse_result(res, like_tids)
    print(musics)

        
    limit = 12

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,OPTIONS,POST,PUT"
    }
    statusCode = 200

    # if userId="", just set all like to 0, frontend won't display it
    results = {
        "count": len(musics),
        "music": musics,
        "message": "fetch more recommendation data successfully"
    }

    return {
        'statusCode': statusCode,
        'headers': headers,
        'body': json.dumps(results)
    }
