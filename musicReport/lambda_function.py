import boto3
import json
import os
import random
import base64
import requests
import numpy as np

db_client = boto3.client('dynamodb')

TOTAL_TRACK = int(os.environ['total_track']) # 22480
client_creds = os.environ['client_creds'] # <clientid:clientsecret> from Spotify Application

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
    if "Item" not in response:
        return ""
    like_tids = response["Item"]["likelist"]["S"]
    return like_tids

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
    
def feature_single_song(track):
    features = np.array([[
                track['acousticness'],
                track['danceability'],
                track['energy'],
                track['instrumentalness'],
                track['key'],
                track['liveness'],
                track['loudness'],
                track['mode'],
                track['speechiness'],
                track['tempo'],
                track['valence'],
            ]])
    return np.round(features, decimals=3)
    
    
def year_dist(trackids, api_key):
    url = "https://api.spotify.com/v1/tracks"
    url_params = {
        "ids": trackids.replace(" ", "")
    }
    headers = {
        'Authorization': 'Bearer %s' % api_key,
        'Accept': 'applicatioin/json',
        'Content-Type': 'application/json'
    }
    response = requests.request('GET', url, headers=headers, params=url_params)
    tracks = response.json()["tracks"]
    years = []
    for track in tracks:
        try:
            years.append(int(track["album"]["release_date"][:4]))
        except:
            pass
    dist = np.histogram(years, bins=10)
    release = {}
    for i, x in enumerate(dist[0]):
        release[dist[1][i]] = int(x)
    return release
    
def get_feature_mtx(trackids, api_key):
    url = "https://api.spotify.com/v1/audio-features"
    url_params = {
        "ids": trackids.replace(" ", "")
    }
    headers = {
        'Authorization': 'Bearer %s' % api_key,
        'Accept': 'applicatioin/json',
        'Content-Type': 'application/json'
    }
    response = requests.request('GET', url, headers=headers, params=url_params)
    tracks = response.json()["audio_features"]
    feature_mtx = np.concatenate([feature_single_song(track) for track in tracks], axis=0)
    return feature_mtx
    
def analyse(trackids):
    api_key = get_token()
    
    feature_mtx = get_feature_mtx(trackids, api_key)
    years = year_dist(trackids, api_key)
    return feature_mtx.mean(0), years


def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,OPTIONS,POST,PUT"
    }

    userId = event["pathParameters"]["userId"]
    like_tids = get_user_like(userId)
    # print(like_tids)
    if like_tids == "":
        return {
            'statusCode': 404,
            'headers': headers,
            'body': json.dumps({"message":"Report: No enough data to generate report because User's like list is empty"})
        }
    user_feature, years = analyse(like_tids)
    
    results = {
        "acousticness":user_feature[0],
        "danceability":user_feature[1],
        "energy":user_feature[2],
        "instrumentalness":user_feature[3],
        "key":user_feature[4],
        "liveness":user_feature[5],
        "loudness":user_feature[6],
        "mode":user_feature[7],
        "speechiness":user_feature[8],
        "tempo": user_feature[9],
        "valence":user_feature[10],
        "release": years,
        "message":"fetch report data successfully"
    }
    
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps(results)
    }
