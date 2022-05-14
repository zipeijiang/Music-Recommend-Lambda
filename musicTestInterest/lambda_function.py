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
    
def get_info(trackids):
    api_key = get_token()
    print(api_key)
    url = "https://api.spotify.com/v1/tracks"
    url_params = {
        "ids": ",".join(trackids)
    }
    headers = {
        'Authorization': 'Bearer %s' % api_key,
        'Accept': 'applicatioin/json',
        'Content-Type': 'application/json'
    }
    response = requests.request('GET', url, headers=headers, params=url_params)
    tracks = response.json()["tracks"]
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
            }
            res.append(item)
    return res

def gen_candidate():
    candidates = random.sample(range(0, TOTAL_TRACK), 40)
    candidates_tids = [idx2tid[str(idx)] for idx in candidates]
    info = get_info(candidates_tids)
    return info
    
def get_current_likelist(userId):
    response = db_client.get_item(
        Key={
            "userId": {
                "S": userId
            }
        },
        TableName='user-like'
    )
    if "Item" in response:
        like_list = (response["Item"]["likelist"]["S"]).replace(" ", "").split(",")
    else:
        like_list = []
    return like_list
    
    
def update_user_like(userId, body):
    original_like_list = get_current_likelist(userId)

    new_like_list = []
    musics = body["music"]
    for music in musics:
        if music["like"] == 1:
            new_like_list.append(music["musicId"])
        elif music["musicId"] in original_like_list:
            original_like_list.remove(music["musicId"])
    if original_like_list == [""]:
        like_list = new_like_list
    else:
        like_list = original_like_list + new_like_list

    mylist = list(dict.fromkeys(like_list))
    like_tids = ",".join(mylist)
    item_dict = {
            "userId": {
                "S": userId
            },
            "likelist": {
                "S": like_tids
            }
        }
    db_response = db_client.put_item(Item=item_dict, TableName='user-like')
    return item_dict["likelist"]["S"]

def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,OPTIONS,POST,PUT"
    }

    statusCode = 200
    if event["httpMethod"] == "GET":

        userId = event["pathParameters"]["userId"]
        
        musics = gen_candidate()

        results = {
            "count": len(musics),
            "music": musics,
            "message": "fetch test interest successfully"
        }

    elif event["httpMethod"] == "POST":
        userId = event["pathParameters"]["userId"]
        body = json.loads(event["body"])
        # body = event["body"]
        
        new_like = update_user_like(userId, body)
        
        
        # body example, 1 means like, 0 normal, -1 dislike
        # {
        #     "count":5,
        #     "music":[
        #         {
        #             "musicId":"xxxx",
        #             "like":1
        #         },
        #         {
        #             "musicId":"xxxx",
        #             "like":-1
        #         },
        #         {
        #             "musicId":"xxxx",
        #             "like":0
        #         }
        #     ]
        # }

        results = {
            "message": "send interest data successfully"
        }

    return {
        'statusCode': statusCode,
        'headers': headers,
        'body': json.dumps(results)
    }
