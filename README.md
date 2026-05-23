# Smart Oil Adulteration Detection System

This repository contains the complete offline IoT + Machine Learning solution for detecting oil adulteration using sensor data and machine learning principles.

## Features

- **Firmware**: NodeMCU (ESP8266) program interacting with TCS34725 (RGB Color), DS18B20 (Temperature), and HX711 (Weight).
- **Backend Hub**: Offline-first, asynchronous thread-safe Flask backend enforcing controlled buffer reads via PySerial.
- **Machine Learning**: Custom hybrid regression model predicting continuously using XGBoost (50%), Random Forest (30%), and KNN (20%).
- **Web App**: State-of-the-art UI with responsive Glassmorphic aesthetic to collect, train, and test data seamlessly.

## Hardware Wiring Guide

| Sensor | Pin/Role | ESP8266 Pin | Notes |
| :--- | :--- | :--- | :--- |
| **TCS34725** | SDA <br> SCL | D2 <br> D1 | I2C standard |
| **DS18B20** | DATA | D5 | 4.7kΩ pull-up resistor from DATA to VCC (3.3V) |
| **HX711** | DT <br> SCK | D6 <br> D7 | Wait to calibrate the hardware `empty_weight` later in UI |

### Load Cell Specifics
- Red → E+
- Black → E-
- White → A-
- Green → A+

---

## 🚀 Setup & Execution

### 1. Embedded Firmware
1. Open `esp8266_firmware/esp8266_firmware.ino` using the Arduino IDE.
2. Install the necessary libraries in the Library Manager: `Adafruit TCS34725`, `OneWire`, `DallasTemperature`, `HX711 Arduino Library`.
3. Flash the code onto the NodeMCU. Ensure a baud rate of `9600`.

### 2. Python Environment
1. Open a terminal in this directory.
2. Create your virtual environment and install the requirements:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Update `SERIAL_PORT` inside `app.py` if your device connects to something other than `COM3`.

### 3. Run the System
1. Launch the server:
   ```bash
   python app.py
   ```
2. Open your browser and navigate to `http://localhost:5000`

### 4. Workflow Rules
- **Training Mode**: Start your dataset with pure configurations (0%), mixed (50%), and highly adulterated samples (100%). You must calibrate the empty and filled container variables before collecting data *each time*.
- **Machine Learning**: Click "Train Model" after populating sufficient data.
- **Testing Mode**: Use the trained `hybrid_model.pkl` to fetch current readings, convert them properly, and calculate the adulteration index securely.
