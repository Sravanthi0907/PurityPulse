import os
import time
import serial
import threading
import pandas as pd2
from flask import Flask, render_template, request, jsonify

from ml_model import train_hybrid_model, predict_adulteration

app = Flask(__name__)

# --- GLOBAL CONTROL VARIABLES ---
collecting = False
samples_collected = 0
current_label = None
empty_weight = None
filled_weight = None

# Hardware config
SERIAL_PORT = 'COM3' # Change if needed on your OS
BAUD_RATE = 9600
FIXED_VOLUME = 100.0 # Default fixed volume in ml
DATASET_PATH = 'dataset.csv'

# Initialize serial globally
ser = None

def get_serial_connection():
    global ser
    if ser is not None and ser.is_open:
        return ser
        
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) # 1 sec timeout
        print(f"Connected to {SERIAL_PORT}")
    except Exception as e:
        ser = None
        print(f"Warning: Serial port {SERIAL_PORT} not opened. {e}")
    
    return ser

serial_lock = threading.Lock()

def get_sensor_data():
    """Read one line from serial, validate and return dictionary."""
    s = get_serial_connection()
    if not s: return None
    
    try:
        line = s.readline().decode('utf-8', errors='ignore').strip()
        if not line: 
            return None
            
        print(f"[LIVE] ESP8266 sent: {line}")
        
        parts = line.split(',')
        if len(parts) == 5:
            temp = float(parts[0])
            weight = float(parts[1])
            r = float(parts[2])
            g = float(parts[3])
            b = float(parts[4])
            return {'temp': temp, 'weight': weight, 'r': r, 'g': g, 'b': b}
        else:
            print(f"[WARN] Malformed parts: {parts}")
            
    except Exception as e:
        print(f"Serial parsing error: {e}")
        return None
    return None

def stable_read():
    """Take 3 valid readings and average them."""
    readings = []
    max_attempts = 20
    attempts = 0
    
    while len(readings) < 3 and attempts < max_attempts:
        data = get_sensor_data()
        if data is not None:
            readings.append(data)
        attempts += 1
        
    if len(readings) < 3:
        return None
        
    avg_data = {
        'temp': sum(r['temp'] for r in readings) / 3.0,
        'weight': sum(r['weight'] for r in readings) / 3.0,
        'r': sum(r['r'] for r in readings) / 3.0,
        'g': sum(r['g'] for r in readings) / 3.0,
        'b': sum(r['b'] for r in readings) / 3.0
    }
    return avg_data

def init_csv():
    """Create CSV with headers if it doesn't exist."""
    if not os.path.exists(DATASET_PATH):
        df = pd.DataFrame(columns=['temp', 'oil_weight', 'density', 'r', 'g', 'b', 'label'])
        df.to_csv(DATASET_PATH, index=False)

def collection_worker(label):
    """Background thread function for exact 100 sample collection"""
    global collecting, samples_collected
    print(f"Starting background collection phase for {label}% adulteration...")
    
    samples_collected = 0
    init_csv()
    
    while collecting and samples_collected < 100:
        with serial_lock: 
            data = stable_read()
            
        if data is None:
            time.sleep(0.5)
            continue
            
        temp = data['temp']
        weight = data['weight']
        r, g, b = data['r'], data['g'], data['b']
        
        oil_weight = weight - empty_weight if empty_weight is not None else weight
        density = oil_weight / FIXED_VOLUME
        
        # Validate rules: temp 0–100, oil_weight > 0, RGB 0–255
        if 0 <= temp <= 100 and oil_weight >= 0:
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            row = pd.DataFrame([[temp, oil_weight, density, r, g, b, label]],
                               columns=['temp', 'oil_weight', 'density', 'r', 'g', 'b', 'label'])
                               
            row.to_csv(DATASET_PATH, mode='a', header=False, index=False)
            
            samples_collected += 1
            print(f"Collected sample {samples_collected}/100")
            
            # User wants a slight delay (0.5 to 1 sec)
            time.sleep(0.5)
        else:
            time.sleep(0.5)
            
    print("Collection completed.")
    collecting = False

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/training')
def training():
    return render_template('training.html')
    
@app.route('/testing')
def testing():
    return render_template('testing.html')

@app.route('/api/calibrate_empty', methods=['POST'])
def handle_calibrate_empty():
    global empty_weight
    s = get_serial_connection()
    if not s: return jsonify({"status": "error", "message": "Serial not connected. Ensure COM3 is free and Arduino Serial Monitor is closed."})
    
    with serial_lock:
        s.reset_input_buffer()
        print("Calibrating Empty Bottle...")
        readings = []
        for _ in range(15): # Allow up to 15 attempts
            data = stable_read()
            if data: 
                readings.append(data['weight'])
                print(f"  -> Valid Empty Reading ({len(readings)}/10): {data['weight']}g")
            else:
                print("  -> Stable read failed, retrying...")
            if len(readings) == 10: break
        
        if len(readings) == 10:
            empty_weight = round(sum(readings) / 10.0, 2)
            print(f"SUCCESS: Empty Bottle set to {empty_weight}g")
            return jsonify({"status": "success", "empty_weight": empty_weight})
        else:
            return jsonify({"status": "error", "message": f"Failed to get 10 readings. The sensor might be stuck or disconnected."})

@app.route('/api/calibrate_filled', methods=['POST'])
def handle_calibrate_filled():
    global filled_weight
    s = get_serial_connection()
    if not s: return jsonify({"status": "error", "message": "Serial not connected. Ensure COM3 is free and Arduino Serial Monitor is closed."})
    
    with serial_lock:
        s.reset_input_buffer()
        print("Calibrating Filled Bottle...")
        readings = []
        for _ in range(15): # Allow up to 15 attempts
            data = stable_read()
            if data: 
                readings.append(data['weight'])
                print(f"  -> Valid Filled Reading ({len(readings)}/10): {data['weight']}g")
            else:
                print("  -> Stable read failed, retrying...")
            if len(readings) == 10: break
        
        if len(readings) == 10:
            filled_weight = round(sum(readings) / 10.0, 2)
            print(f"SUCCESS: Filled Bottle set to {filled_weight}g")
            return jsonify({"status": "success", "filled_weight": filled_weight})
        else:
            return jsonify({"status": "error", "message": f"Failed to get 10 stable readings. The sensor might be stuck or disconnected."})

@app.route('/api/start_training', methods=['POST'])
def handle_start_training():
    global collecting, current_label
    
    req_data = request.json
    label = int(req_data.get('label', -1))
    
    if label not in [0, 50, 100]:
        return jsonify({"status": "error", "message": "Invalid Adulteration % (must literally be 0, 50, or 100)."})
        
    if empty_weight is None or filled_weight is None:
        return jsonify({"status": "error", "message": "Must calibrate both Empty and Filled bottles first."})
        
    if collecting:
        return jsonify({"status": "error", "message": "System is already collecting training data."})
        
    s = get_serial_connection()
    if not s:
         return jsonify({"status": "error", "message": "Serial port is disconnected. Close Arduino Serial monitor."})
        
    with serial_lock:    
        s.reset_input_buffer()
        
    collecting = True
    current_label = label
    
    # Run the bounded 100 loops
    thread = threading.Thread(target=collection_worker, args=(current_label,))
    thread.daemon = True # so it doesn't block shutdown
    thread.start()
    
    return jsonify({"status": "success", "message": f"Started collecting samples for {label}%."})

@app.route('/api/status', methods=['GET'])
def get_status():
    global collecting, samples_collected, empty_weight, filled_weight
    return jsonify({
        "collecting": collecting,
        "samples_collected": samples_collected,
        "empty_weight": empty_weight if empty_weight else "Not Set",
        "filled_weight": filled_weight if filled_weight else "Not Set"
    })

@app.route('/api/train_model', methods=['POST'])
def handle_train_model():
    success, message = train_hybrid_model(DATASET_PATH, 'hybrid_model.pkl')
    status = "success" if success else "error"
    return jsonify({"status": status, "message": message})

@app.route('/api/predict', methods=['POST'])
def handle_predict():
    s = get_serial_connection()
    if not s: return jsonify({"status": "error", "message": "Serial not connected. Close Arduino Serial monitor."})
    
    # We require an empty calibration at the minimum for zeroing out. Filled is good but volume limits density directly
    if empty_weight is None or filled_weight is None:
        return jsonify({"status": "error", "message": "Calibrate the empty and filled weights before testing."})
        
    with serial_lock: 
        s.reset_input_buffer()
        data = stable_read()
        
    if not data:
        return jsonify({"status": "error", "message": "Sensor read failure (no stable values)."})
        
    temp = data['temp']
    weight = data['weight']
    r, g, b = data['r'], data['g'], data['b']
    
    oil_weight = weight - empty_weight
    density = oil_weight / FIXED_VOLUME
    
    # Extract prediction
    features = [temp, oil_weight, density, r, g, b]
    
    prediction, err = predict_adulteration(features, 'hybrid_model.pkl')
    
    if err is not None:
        return jsonify({"status": "error", "message": err})
        
    return jsonify({
        "status": "success",
        "adulteration_percentage": prediction,
        "data": {
            "temp": round(temp, 2),
            "oil_weight": round(oil_weight, 2),
            "density": round(density, 2),
            "r": round(r, 0),
            "g": round(g, 0),
            "b": round(b, 0)
        }
    })

if __name__ == '__main__':
    # Start app threadable mode explicitly
    app.run(debug=True, threaded=True, host='0.0.0.0', port=5000)
