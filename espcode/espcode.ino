#include <Wire.h>
#include <Adafruit_TCS34725.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <HX711.h>

// Pins based on NodeMCU specs
#define ONE_WIRE_BUS D5
#define LOADCELL_DOUT_PIN D6
#define LOADCELL_SCK_PIN D7

// Init DS18B20 Temperature
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// Init HX711 Load Cell
HX711 scale;
float calibration_factor = 197.9;

// Init TCS34725 Color Sensor
Adafruit_TCS34725 tcs = Adafruit_TCS34725(TCS34725_INTEGRATIONTIME_50MS, TCS34725_GAIN_4X);

void setup() {
  // Serial must be exactly 9600 for the python script
  Serial.begin(9600);
  delay(10);
  
  // Wire begin explicitly on D2(SDA) and D1(SCL)
  Wire.begin(D2, D1);
  
  // Setup temp sensor
  sensors.begin();
  
  // Setup load cell
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(calibration_factor);
  
  if (scale.is_ready()) {
    scale.tare(); 
  }
  
  // Setup color sensor
  tcs.begin();
}

void loop() {
  float avg_temp = 0.0;
  float avg_weight = 0.0;
  float avg_r = 0.0, avg_g = 0.0, avg_b = 0.0;
  
  // Take 3 readings and average
  for(int i = 0; i < 3; i++) {
    yield(); // Feed watchdog timer explicitly
    
    // Read Temperature
    sensors.requestTemperatures();
    avg_temp += sensors.getTempCByIndex(0);
    
    // Read Weight safely (HX711 can cause infinite WDT hang if disconnected)
    if (scale.is_ready()) {
      avg_weight += scale.get_units(1);
    }
    
    // Read Color (0-255 mapped correctly by Adafruit function)
    float r = 0, g = 0, b = 0;
    tcs.getRGB(&r, &g, &b);
    avg_r += r;
    avg_g += g;
    avg_b += b;
    
    delay(100);
  }
  
  avg_temp /= 3.0;
  avg_weight /= 3.0;
  avg_r /= 3.0;
  avg_g /= 3.0;
  avg_b /= 3.0;
  
  // Format exactly: temp,weight,r,g,b
  Serial.print(avg_temp, 2);
  Serial.print(",");
  Serial.print(avg_weight, 2);
  Serial.print(",");
  Serial.print(avg_r, 2);
  Serial.print(",");
  Serial.print(avg_g, 2);
  Serial.print(",");
  Serial.println(avg_b, 2);

  // Total loop is ~300ms + 650ms = ~1 sec cycle time
  delay(650);
}
