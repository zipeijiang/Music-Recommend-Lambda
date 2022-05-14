import boto3
import json
import requests
from requests_aws4auth import AWS4Auth
from opensearchpy import OpenSearch, RequestsHttpConnection
import numpy as np

TOTAL_TRACK = 22480
region = 'us-east-1' # For example, us-west-1
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
url = "https://search-embedding-nelipnibmic5jinufn2etf6nre.us-east-1.es.amazonaws.com/embedding/_msearch"

s3_client = boto3.client('s3')

idx2tid_data = (s3_client.get_object(Bucket='model-data-proj', Key='idx2tid.json')['Body']).read().decode('utf-8')
idx2tid = json.loads(idx2tid_data)

def query_str(tid):
    query = {'query': {'match': {"_id": tid}}}
    return json.dumps(query)
    
def build_search_body(tids):
    res = ""
    for tid in tids:
        res = res + "{}\n" + query_str(tid) + "\n"
    return res
    
def extrac_embedding(hit):
    return hit["hits"]["hits"][0]["_source"]["embedding"]
    
def httpsearch(tids):
    data_as_str = build_search_body(tids)
                    
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    r = requests.post(url, headers=headers, auth=awsauth, data=data_as_str)
    query_results = json.loads(r.text)["responses"]
    buf = ""
    for hit in query_results:
        buf = buf + hit["hits"]["hits"][0]["_source"]["embedding"] + ","
    embedding = np.fromstring(buf[:-1], sep=",")
    return embedding.reshape(-1, 64)


def lambda_handler(event, context):
    tids = ["63ZKsPTw5i9jPPp8tAefvR", "0dcbzDSWBOgyIONbQFsiTz"]
    candidates = np.random.randint(0, TOTAL_TRACK, size=100)
    candidates_tids = [idx2tid[str(idx)] for idx in candidates]
    right = httpsearch(candidates_tids)
    print(right.shape)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
