import json
import sys
import logging
import spotipy
import spotipy.util as util
import requests
import boto3
from spotipy.oauth2 import SpotifyClientCredentials
 
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

db_client = boto3.client('dynamodb')

def get_user_like(userId, limit):
    response = db_client.get_item(
        Key={
            'userId': {
                'S': userId,
            }, 

        },
        TableName='user-like',
        AttributesToGet=['likelist']
    )
    if "Item" not in response:
        response = db_client.put_item(
            TableName='user-like',
            Item={
                'userId': {
                    'S': userId,
                },
                'likelist':{
                    'S': "",
                }
            }
            )
        return ""
    like_tids = response["Item"]["likelist"]["S"].replace(', ', ',') 
    return like_tids

def put_user_like(userId, tid, add):
    new_tids = ""
    response = db_client.get_item(
        Key={
            'userId': {
                'S': userId,
            },

        },
        TableName='user-like',
        AttributesToGet=['likelist']
    )
    if "Item" in response:
        if add:
            if new_tids == "":
                new_tids = tid
            else:
                new_tids = new_tids + ", " + tid
        else:   
            new_tids = response["Item"]["likelist"]["S"].split(",")
            new_tids.remove(tid)
            new_tids = ", ".join(new_tids) 
            
    elif add:
        new_tids = tid
    response = db_client.put_item(
        TableName='user-like',
        Item={
            'userId': {
                'S': userId,
            },
            'likelist':{
                'S': new_tids,
            }
        }
        )
    return 200 

def put_music_like(tid, add):
    response = db_client.get_item(
        Key={
            'musicId': {
                'S': tid,
            },

        },
        TableName='music-like',
        AttributesToGet=['count']
    )
    if add:
        if "Item" not in response:
            count = str(1)
        else:
            count = str(int(response["Item"]["count"]["N"]) + 1)
    else:
        if "Item" not in response:
            count = str(0)
        else:
            count = str(int(response["Item"]["count"]["N"]) - 1) 
    response = db_client.put_item(
        TableName='music-like',
        Item={
            'musicId': {
                'S': tid,
            },
            'count':{
                'N': count,
            }
        }
        )
    return 200 
    
def get_music_count(tid):
    response = db_client.get_item(
        Key={
            'musicId': {
                'S': tid,
            },

        },
        TableName='music-like',
        AttributesToGet=['count']
    )
    if "Item" not in response:
        count = 0
    else:
        count = int(response["Item"]["count"]["N"]) 
    return count

def get_music_info(tids):
    tracks = ['spotify:track:'+tid for tid in tids]
    results = spotify.tracks(tracks)
    return results  

def extract(data, page, tids, limit):
    result = []
    if len(data) <= (page-1)*limit:
        return result
    
    for item in data[(page-1)*limit: page*limit]:
        obj = {
                "musicId": item['id'],
                "musicName": item['name'],
                "artistName": [i['name'] for i in item['artists']],
                "imageUrl": item["album"]['images'][0]['url'] if item["album"] and item["album"]['images'] and len(item["album"]['images'])>0 else '',
                "musicUrl": item['preview_url'],
                "like": 1 if item['id'] in tids else 0 
            }
        result.append(obj)
    return result

def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,OPTIONS,POST,PUT"
    }

    statusCode = 200
    userId = event["pathParameters"]["userId"]
    #userId = 'berkaa87' 
    page = 1
    limit = 12
    if event["queryStringParameters"] and "page" in event["queryStringParameters"]:
        page = int(event["queryStringParameters"]["page"])

    tids = get_user_like(userId, limit).split(',') 
    print(tids) 
    tids = list(set(tids)) 
    print(tids)  
    if tids[0] == "":
        results = {
            "count": 0,
            "music": [],
            "message": "fetch user like data successfully"
        } 
    else:
        r = get_music_info(tids)['tracks']
        music = extract(r, page, tids, limit) 
    
        results = {
            "count": len(tids),
            "music": music, 
            "message": "fetch user like data successfully"
        }
        
    return {
        'statusCode': statusCode,
        'headers': headers,
        'body': json.dumps(results) 
    }

