import boto3
import json

# Connection to our table
table = boto3.resource('dynamodb').Table('GuardianIncidents')

def lambda_handler(event, context):
    # 1. Capture the VIN from the link (?vin=ABC123)
    params = event.get('queryStringParameters', {})
    vin = params.get('vin')
    
    if not vin:
        return {'statusCode': 400, 'body': 'Error: No VIN found in link.'}

    # 2. Update the status to 'RESOLVED' automatically
    table.update_item(
        Key={'VIN': vin},
        UpdateExpression="SET #s = :val",
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':val': 'RESOLVED'}
    )
    
    # 3. What the user sees in their browser after clicking
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': f"<h1>Safe Status Confirmed</h1><p>VIN {vin} has been marked as safe. No emergency services will be sent.</p>"
    }
