import boto3
import json
import time
import random
import uuid
from datetime import datetime, timezone

# Configuration
STREAM_NAME = 'GuardianStream-VehicleData'
REGION = 'us-east-1'

kinesis_client = boto3.client('kinesis', region_name=REGION)

# 1. Create a fleet of 5 distinct vehicles
FLEET_VINS = [str(uuid.uuid4())[:8].upper() for _ in range(5)]

def generate_vehicle_data(vin, scenario="NORMAL"):
    # Using timezone-aware UTC for professional standards
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Initialize default sensor values
    tilt_angle = round(random.uniform(-2.0, 2.0), 2) # Slight tilt for turns/hills
    airbag_deployed = False
    
    if scenario == "NORMAL":
        g_force = round(random.uniform(0.1, 1.5), 2)
        speed = round(random.uniform(40, 80), 2)
        heartbeat = random.randint(65, 95)
    
    elif scenario == "CRASH_CONSCIOUS":
        g_force = round(random.uniform(8.5, 12.0), 2)
        speed = round(random.uniform(0, 10), 2) # Rapid deceleration
        heartbeat = random.randint(90, 120)    # Elevated due to stress
        # 20% chance of airbag in moderate crash
        airbag_deployed = random.random() < 0.20
        tilt_angle = round(random.uniform(-10.0, 10.0), 2)
        
    elif scenario == "CRASH_UNCONSCIOUS":
        g_force = round(random.uniform(12.0, 25.0), 2) # Severe impact
        speed = 0.0
        heartbeat = 0 # Life-threatening state
        
        # Sensor Fusion: Severe crashes often involve rollover or airbags
        airbag_deployed = True # Airbags almost always deploy at high G-force
        # 50% chance the car is resting on its side or roof
        if random.random() > 0.5:
            tilt_angle = round(random.uniform(45.0, 180.0), 2) 
        else:
            tilt_angle = round(random.uniform(-5.0, 5.0), 2)

    data = {
        "vin": vin,
        "g_force": g_force,
        "speed": speed,
        "heartbeat": heartbeat,
        "tilt_angle": tilt_angle,         
        "airbag_deployed": airbag_deployed, 
        "scenario_type": scenario,
        "timestamp": timestamp
    }
    return data

def run_fleet_generator():
    print(f"--- 2026 Guardian Fleet Active ---")
    print(f"Monitoring: {FLEET_VINS}")
    
    try:
        while True:
            selected_vin = random.choice(FLEET_VINS)
            
            # Probability Logic
            chance = random.random()
            if chance < 0.03:    # 3% Severe Crash
                scenario = "CRASH_UNCONSCIOUS"
            elif chance < 0.08:  # 5% Moderate Crash
                scenario = "CRASH_CONSCIOUS"
            else:
                scenario = "NORMAL"
                
            payload = generate_vehicle_data(selected_vin, scenario)
            
            # Send to Kinesis
            kinesis_client.put_record(
                StreamName=STREAM_NAME,
                Data=json.dumps(payload),
                PartitionKey=selected_vin
            )
            
            # Enhanced Console Output for debugging Sensor Fusion
            status_line = f"[{scenario}] VIN: {selected_vin} | G: {payload['g_force']} | Airbag: {payload['airbag_deployed']} | Tilt: {payload['tilt_angle']}°"
            print(status_line)
            
            time.sleep(0.5) 
            
    except KeyboardInterrupt:
        print("\nSimulation Ended.")

if __name__ == "__main__":
    run_fleet_generator()
