import json
import boto3 

def send_email(userId, email): 
    client = boto3.client("ses",region_name="us-east-1")  
    raw = """Hi,
    
    Please use the link to reset passworrd:
        https://project-frontend222.s3.amazonaws.com/build2/index.html#/forget?userId=%s

    Regards,
    Music team
    
    """
    body = raw%(userId)
    client.send_email(
	    Source = 'zipeijiang@gmail.com',
	    Destination = {
		    'ToAddresses': [
			    email
		    ]
	    },
	    Message = {
		    'Subject': {
			    'Data': 'Music Password Reset', 
			    'Charset': 'UTF-8'
		    },
		    'Body': {
			    'Text':{
				    'Data': body,
				    'Charset': 'UTF-8' 
			    }
		    }
	    }
    )
    return 200, {
        "message": "email sent successfully"
    }

def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,OPTIONS,POST,PUT"
    }
    
    statusCode = 400
    #body = event["body"]
 
    body = json.loads(event['body'])  
    print(body)
    # body example:
    # {
    #     "email":"xxxx@xxx.com"
    # }

    # send email
    email = body["email"]
    userId = body["userId"]

    # send email(can use the joanndmw.com domain in SES)
    # user click the link(http://project-frontend222.s3-website-us-east-1.amazonaws.com/build/index.html#/forget)
    # may add cookie to the link, I don't know :/
    statusCode, results = send_email(userId, email) 
    #_, results = send_email('fdgdf', 'zipeijiang@gmail.com')   
    
    return {
        "statusCode": statusCode,
        "headers": headers,
        "body": json.dumps(results)
    }
