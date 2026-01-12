import json
import base64
import boto3
import os
from datetime import datetime, timedelta, timezone

# 1. INITIALIZATION 
EMERGENCY_ARN = os.environ.get('EMERGENCY_TOPIC_ARN')
WARNING_ARN = os.environ.get('WARNING_TOPIC_ARN')
DISMISS_URL = os.environ.get('DISMISS_URL')

dynamodb = boto3.resource('dynamodb').Table('GuardianIncidents')
sns = boto3.client('sns')

def lambda_handler(event, context):
    # --- TRIGGER TYPE A: SCHEDULED TIMER (EventBridge) ---
    if event.get('source') == 'aws.events':
        print("Watchdog Triggered: Checking for unresponsive drivers...")
        check_for_escalations()
        return {'statusCode': 200, 'body': 'Escalation check complete.'}

    # --- TRIGGER TYPE B: LIVE CRASH DATA (Kinesis) ---
    if 'Records' in event:
        for record in event['Records']:
            try:
                data = base64.b64decode(record['kinesis']['data']).decode('utf-8')
                payload = json.loads(data)
                
                vin = payload['vin']
                g_force = payload['g_force']
                heartbeat = payload['heartbeat']
                
                # --- NEW SENSOR DATA ---
                airbag = payload.get('airbag_deployed', False)
                tilt = abs(payload.get('tilt_angle', 0))

                # --- SENSOR FUSION TRIAGE LOGIC ---
                if g_force > 8.0:
                    # PRIORITY 1: Instant Escalation (Airbags, Rollover, or No Pulse)
                    if airbag or tilt > 60 or heartbeat == 0:
                        reason = "Airbag Deployed" if airbag else "Rollover Detected" if tilt > 60 else "Unconscious Occupant"
                        process_incident(vin, EMERGENCY_ARN, f"CODE RED: {reason}!", "ESCALATED")
                    
                    # PRIORITY 2: Warning (Conscious occupant, monitor for 15s)
                    else:
                        process_incident(vin, WARNING_ARN, "WARNING: High impact detected. Are you okay?", "WARNING")
                
                else:
                    # Routine health ping
                    update_vehicle_status(vin, "NORMAL")
                    
            except Exception as e:
                print(f"Error processing record: {e}")

    return {'statusCode': 200, 'body': 'Processed'}

def process_incident(vin, topic_arn, message_text, status):
    """Sends customized alerts and updates DynamoDB state"""
    try:
        subject = f"URGENT: Guardian Emergency ({vin})" if status == "ESCALATED" else f"Guardian Safety Alert ({vin})"
        
        if status == "WARNING":
            body = f"{message_text}\n\nCLICK TO DISMISS: {DISMISS_URL}?vin={vin}"
        else:
            body = f"{message_text}\n\nDispatching services to your GPS coordinates."

        sns.publish(TopicArn=topic_arn, Message=body, Subject=subject)

        item = {
            'VIN': vin,
            'status': status,
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
        
        if status == "WARNING":
            # Set a 15-second window for dismissal
            item['expiry_time'] = (datetime.now(timezone.utc) + timedelta(seconds=15)).isoformat()
        
        dynamodb.put_item(Item=item)
        print(f"[{status}] State saved for {vin}")

    except Exception as e:
        print(f"Incident Error: {e}")

def check_for_escalations():
    """Autonomous Watchlog: Escalates non-responses"""
    now = datetime.now(timezone.utc).isoformat()
    response = dynamodb.scan(
        FilterExpression="#s = :s AND expiry_time < :t",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": "WARNING", ":t": now}
    )

    for item in response.get('Items', []):
        vin = item['VIN']
        print(f"!!! WATCHDOG ESCALATION: {vin}")
        process_incident(vin, EMERGENCY_ARN, "AUTOMATIC ESCALATION: Occupant unresponsive to safety check.", "ESCALATED")

def update_vehicle_status(vin, status):
    try:
        # Check current state first
        current = dynamodb.get_item(Key={'VIN': vin}).get('Item', {})
        current_status = current.get('status', 'NONE')

        # If already in an emergency state, do NOT overwrite with 'NORMAL'
        if current_status in ["WARNING", "ESCALATED"] and status == "NORMAL":
            return 

        dynamodb.put_item(Item={
            'VIN': vin,
            'status': status,
            'last_updated': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        print(f"Status update error: {e}")
