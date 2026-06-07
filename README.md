# PurityPulse — IoT-Based Oil Adulteration Detection System 

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9–3.11-blue?logo=python" alt="Python 3.9–3.11"/>
  <img src="https://img.shields.io/badge/Flask-2.x%2F3.x-black?logo=flask" alt="Flask"/>
  <img src="https://img.shields.io/badge/XGBoost-1.x%2F2.x-orange?logo=xgboost" alt="XGBoost"/>
  <img src="https://img.shields.io/badge/scikit--learn-1.x-blue?logo=scikit-learn" alt="scikit-learn"/>
  <img src="https://img.shields.io/badge/ESP8266-NodeMCU-red?logo=espressif" alt="ESP8266"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="MIT License"/>
</p>

**PurityPulse** is an end-to-end, offline-first IoT and Machine Learning platform designed to detect oil adulteration in real-time. By combining physical sensor measurements—**temperature** (DS18B20), **mass/density** (HX711 Load Cell), and **optical spectrum characteristics** (TCS34725 RGB sensor)—with a hybrid ensemble machine learning model, PurityPulse classifies and quantifies the degree of adulteration instantly.

---

## Key Features

| Feature | Description |
|---|---|
| **Multi-Sensor Telemetry** | Seamless integration with temperature, load cell (weight), and RGB color sensors. |
| **Real-Time Calibration** | Dynamic empty and filled bottle weight calibration to calculate oil density based on volume. |
| **Asynchronous Data Logger** | Automated data collector capturing exactly 100 samples in a background thread for model training. |
| **Hybrid Machine Learning** | Blends XGBoost (50%), Random Forest (30%), and K-Nearest Neighbors (20%) Regressors for robust predictions. |
| **Glassmorphic Web Dashboard** | Modern web UI styled with dark-mode gradients, smooth hover animations, and color-coded results. |

---

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Outfit Typeface (Google Fonts), Glassmorphism-style UI
- **Backend**: Flask (Python 3.9–3.11), PySerial (thread-safe hardware data polling)
- **Firmware / Hardware**: Arduino IDE, ESP8266 (NodeMCU), I2C protocol, OneWire protocol
- **Sensors**: TCS34725 (RGB Color Sensor), DS18B20 (Waterproof Temperature Probe), HX711 (Weight/Load Cell Amplifier)
- **Machine Learning**: XGBoost (XGBRegressor), scikit-learn (RandomForestRegressor, KNeighborsRegressor), pandas, numpy, joblib (model storage)

---

## Project Structure

```
PURITYPULSE/
│
├── espcode/
│   └── espcode.ino         ← ESP8266 firmware (reads sensors, averages, sends serial)
│
├── templates/
│   ├── index.html          ← Landing dashboard with Training/Testing routes
│   ├── training.html       ← Calibration + data collection + ML training console
│   └── testing.html        ← Real-time sample analysis & ML prediction dashboard
│
├── app.py                  ← Flask server (manages calibration, serial buffer, & API routes)
├── ml_model.py             ← ML pipeline (XGBoost, Random Forest, & KNN training/inference)
├── dataset.csv             ← Collected sensor readings and labels
├── hybrid_model.pkl        ← Serialized hybrid regressor models
├── requirements.txt        ← Python dependencies
└── README.md               ← Documentation
```

---

## Hardware Wiring Guide

| Sensor | Pin/Role | ESP8266 Pin | Notes |
| :--- | :--- | :--- | :--- |
| **TCS34725** | SDA <br> SCL | D2 <br> D1 | I2C standard communication |
| **DS18B20** | DATA | D5 | Requires a 4.7kΩ pull-up resistor from DATA to VCC (3.3V) |
| **HX711** | DT <br> SCK | D6 <br> D7 | High-precision load cell amplifier |

### Load Cell Specifics (HX711 to Load Cell)
- Red Pin → E+
- Black Pin → E-
- White Pin → A-
- Green Pin → A+

---

## Mathematics & Calibration Logic

### 1. Mass & Density Calculation
Before capturing training data or performing prediction, the user must run calibration steps:
1. **Calibrate Empty Bottle**: Place the empty container on the scale. The system averages 10 readings to establish the `empty_weight` baseline.
2. **Calibrate Filled Bottle**: Place a container filled with exactly 100 ml of pure oil on the scale. The system averages 10 readings to establish the `filled_weight` baseline.

These calibrations allow the backend to dynamically subtract tare weight and estimate oil density:
$$\text{Oil Weight} = \text{Total Weight} - \text{Empty Weight}$$
$$\text{Density} = \frac{\text{Oil Weight}}{\text{Fixed Volume (100 ml)}}$$

### 2. Hybrid Model Regression Formula
The system utilizes a weighted hybrid regressor model:
$$\text{Final Prediction} = 0.5 \times \text{XGBoost} + 0.3 \times \text{Random Forest} + 0.2 \times \text{KNN}$$

The predicted output is bounded between $0.0\%$ (Pure) and $100.0\%$ (Adulterated):
$$\text{Result} = \max\left(0.0, \min\left(100.0, \text{Final Prediction}\right)\right)$$

---

## Installation

### Prerequisites
- **Python 3.9 – 3.11** — required for XGBoost and scikit-learn
- **Arduino IDE** — for flashing the NodeMCU board
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/PurityPulse.git
cd PurityPulse
```

### 2. Create a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Complete Workflow (from scratch)

Follow these steps **in order** to go from a fresh clone to a fully trained application.

### Step 1 — Embedded Firmware Setup (`espcode.ino`)
1. Open `espcode/espcode.ino` using the Arduino IDE.
2. Install the necessary libraries in the Library Manager:
   - `Adafruit TCS34725`
   - `OneWire`
   - `DallasTemperature`
   - `HX711 Arduino Library`
3. Flash the code onto the NodeMCU. Keep the micro-USB connected to your computer. Ensure a baud rate of `9600`.

### Step 2 — Run the Flask Server (`app.py`)
1. Open `app.py` and verify the `SERIAL_PORT` variable (default is `'COM3'`). Update it matching your system's serial port (e.g. `COM4` or `/dev/ttyUSB0`).
2. Run the application:
   ```bash
   python app.py
   ```
3. Open your browser and navigate to: **http://127.0.0.1:5000**

### Step 3 — Collect Training Data
1. Select **Training Mode** from the landing dashboard.
2. Calibrate the **Empty Bottle** and **Filled Bottle** weights.
3. Select the target Adulteration percentage from the dropdown:
   - `0%` (Pure)
   - `50%` (Mixed)
   - `100%` (Fake)
4. Click **Start Collection**. The system will asynchronously capture exactly 100 sensor readings in a background thread and append them to `dataset.csv`.
5. Repeat for all three labels (0%, 50%, 100%) to complete your dataset.

### Step 4 — Train the Model
1. On the **Training Mode** screen, click **Train Model**.
2. The ML pipeline (`ml_model.py`) will automatically train the `XGBoost`, `Random Forest`, and `KNN` regressors on the collected data.
3. The model parameters will be saved as `hybrid_model.pkl`.

### Step 5 — Predict Adulteration in Testing Mode
1. Navigate to **Testing Mode** via the navigation menu.
2. Calibrate weights for the current session.
3. Place your unknown oil sample on the sensor rig.
4. Click **Predict Adulteration**.
5. The UI displays the adulteration prediction dynamically:
   - 🟢 **Pure / Low Risk** (< 20%): Clean green gradient.
   - 🟡 **Moderate Adulteration** (20% - 70%): Warning amber gradient.
   - 🔴 **High Adulteration / Fake** (>= 70%): Danger red gradient.
   - You also get instant readouts for Temperature, Net Weight, Density, and RGB color channels.
