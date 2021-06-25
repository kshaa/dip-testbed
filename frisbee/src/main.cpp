#include <Arduino.h>
#include <Adafruit_LSM6DSOX.h>
#include <Adafruit_LIS3MDL.h>
#include <bluefruit.h>
#include <ble_hci.h>
#include "frisbee_config.hpp"
#include "frisbee_engine.hpp"
#include "lsm6ds_sensor.hpp"
#include "lis3mdl_sensor.hpp"

// Sensor services
Adafruit_LSM6DSOX lsm6ds;
Adafruit_LIS3MDL  lis3mdl;

// Bluetooth services
BLEDis  blDevice;
BLEBas  blBattery;
BLEUart blUART;

void blConnectCallback(uint16_t conn_handle) {
  BLEConnection* connection = Bluefruit.Connection(conn_handle);
  char centralName[32] = "";
  connection->getPeerName(centralName, sizeof(centralName));
  Serial.println("Device '" + String(centralName) + "' connected to frisbee, advertising stopped");
}

void blDisconnectCallback(uint16_t conn_handle, uint8_t reason) {
  BLEConnection* connection = Bluefruit.Connection(conn_handle);
  char centralName[32] = "";
  connection->getPeerName(centralName, sizeof(centralName));
  Serial.print("Device '" + String(centralName) + "' disconnected from frisbee with reason '");
  Serial.print(reason, HEX);
  Serial.print("', advertising restarted");
  Serial.println();
}

void setup(void) {
  // Initialize and wait for serial port
  Serial.begin(ADA_NRF52_BAUD_RATE);
  while (!Serial) delay(SERVICE_INIT_TIMEOUT_MS);
  Serial.println("Initializing iot-frisbee with Adafruit nRF52832, LSM6DS, LIS3MDL!");

  // Initiate communication w/ LSM6DS sensor over I2C
  runUntilSuccessSerial(
    [](void) { return lsm6ds.begin_I2C(); },
    "LSM6DS chip I2C connection",
    SERVICE_INIT_TIMEOUT_MS
  );

  // Initiate communication w/ LIS3MDL sensor over I2C
  runUntilSuccessSerial(
    [](void) { return lis3mdl.begin_I2C(); },
    "LIS3MDL chip I2C connection",
    SERVICE_INIT_TIMEOUT_MS
  );

  // Configure LSM6DS accelerometer
  lsm6ds.setAccelRange(LSM6DS_ACCEL_RANGE);
  lsm6ds_accel_range_t lsm6dsAccelRange = lsm6ds.getAccelRange();
  Serial.printf("Setting LSM6DS accelerometer range to: %s\r\n", lsm6dsAccelRangeText(lsm6dsAccelRange));

  lsm6ds.setAccelDataRate(LSM6DS_ACCEL_DATA_RATE);
  lsm6ds_data_rate_t lsm6dsAccelDataRate = lsm6ds.getAccelDataRate();
  Serial.printf("Setting LSM6DS accelerometer data rate to: %s\r\n", lsm6dsDataRateText(lsm6dsAccelDataRate));

  // Configure LSM6DS gyroscope
  lsm6ds.setGyroRange(LSM6DS_GYRO_RANGE);
  lsm6ds_gyro_range_t lsm6dsGyroRange = lsm6ds.getGyroRange();
  Serial.printf("Setting LSM6DS gyro range to: %s\r\n", lsm6dsGyroRangeText(lsm6dsGyroRange));

  lsm6ds.setGyroDataRate(LSM6DS_GYRO_DATA_RATE);
  lsm6ds_data_rate_t lsm6dsGyroDataRate = lsm6ds.getGyroDataRate();
  Serial.printf("Setting LSM6DS gyro data rate to: %s\r\n", lsm6dsDataRateText(lsm6dsGyroDataRate));
  
  // Configure LIS3MDL magnetometer
  lis3mdl.setRange(LIS3MDL_MAGNET_RANGE);
  lis3mdl_range_t lis3mdlMagnetRange = lis3mdl.getRange();
  Serial.printf("Setting LSM6DS magnetometer range to: %s\r\n", lis3mdlMagnetRangeText(lis3mdlMagnetRange));

  lis3mdl.setDataRate(LIS3MDL_MAGNET_DATA_RATE);
  lis3mdl_dataRate_t lis3mdlMagnetDataRate = lis3mdl.getDataRate();
  Serial.printf("Setting LSM6DS magnetometer data rate to: %s\r\n", lis3mdlDataRateText(lis3mdlMagnetDataRate));

  lis3mdl.setPerformanceMode(LIS3MDL_PERFORMANCE_MODE);
  lis3mdl_performancemode_t lis3mdlMagnetPerformanceMode = lis3mdl.getPerformanceMode();
  Serial.printf("Setting LSM6DS magnetometer performance mode to: %s\r\n", lis3mdlMagnetPerformanceModeText(lis3mdlMagnetPerformanceMode));

  lis3mdl.setOperationMode(LIS3MDL_OPERATION_MODE);
  lis3mdl_operationmode_t lis3mdlMagnetOperationMode = lis3mdl.getOperationMode();
  Serial.printf("Setting LSM6DS magnetometer operation mode to: %s\r\n", lis3mdlMagnetOperationModeText(lis3mdlMagnetOperationMode));

  lis3mdl.setIntThreshold(LIS3MDL_INT_TRESHOLD);
  lis3mdl.configInterrupt(
    LIS3MDL_ENABLE_X,
    LIS3MDL_ENABLE_Y,
    LIS3MDL_ENABLE_Z,
    LIS3MDL_ENABLE_POLARITY,
    LIS3MDL_ENABLE_LATCH,
    LIS3MDL_ENABLE_INTERRUPTS);

  // Configure Bluetooth connectivity & event handlers
  Bluefruit.autoConnLed(BL_AUTO_CONN_LED);
  runUntilSuccessSerial(
    [](void) { return Bluefruit.begin(); },
    "Bluefruit chip",
    SERVICE_INIT_TIMEOUT_MS
  );
  Bluefruit.setName(BL_DEVICE_NAME);
  Bluefruit.Periph.setConnectCallback(blConnectCallback);
  Bluefruit.Periph.setDisconnectCallback(blDisconnectCallback);

  // Configure Bluetooth device information
  blDevice.setManufacturer(BL_DEVICE_MANUFACTURER);
  blDevice.setModel(BL_DEVICE_MODEL);
  runUntilSuccessSerial(
    [](void) { return blDevice.begin() == ERROR_NONE; },
    "Bluetooth device information service",
    SERVICE_INIT_TIMEOUT_MS
  );

  // Configure Bluetooth UART service
  runUntilSuccessSerial(
    [](void) { return blUART.begin() == ERROR_NONE; },
    "Bluetooth UART service",
    SERVICE_INIT_TIMEOUT_MS
  );

  // Configure Bluetooth battery service
  runUntilSuccessSerial(
    [](void) { return blBattery.begin() == ERROR_NONE; },
    "Bluetooth battery level service",
    SERVICE_INIT_TIMEOUT_MS
  );

  // Configure device advertisement
  Bluefruit.Advertising.addFlags(BL_ADVERTISEMENT_FLAGS);
  Bluefruit.Advertising.addTxPower();
  Bluefruit.Advertising.addService(blUART);
  Bluefruit.Advertising.restartOnDisconnect(true);
  // Bluefruit.Advertising.setIntervalMS(BL_FAST_RETRY_INTERVAL_MS, BL_SLOW_RETRY_INTERVAL_MS);
  // Bluefruit.Advertising.setFastTimeout(BL_FAST_TIMEOUT_S);
  Bluefruit.ScanResponse.addName();
  runUntilSuccessSerial(
    [](void) { return Bluefruit.Advertising.start(); },
    "Bluetooth advertisement service",
    SERVICE_INIT_TIMEOUT_MS
  );
}

void loop() {
  // Read sensor values
  sensors_event_t accel, gyro, mag, temp;
  lsm6ds.getEvent(&accel, &gyro, &temp);
  lis3mdl.getEvent(&mag);
  unsigned long time = millis();

  // Forward data from HW Serial to BLEUART
  while (Serial.available())
  {
    // Delay to wait for enough input, since we have a limited transmission buffer
    delay(10);

    uint8_t buf[64];
    int count = Serial.readBytes(buf, sizeof(buf));
    // Serial.printf("\t\tSerial: %d", buf);
    // Serial.println();
    blUART.write(buf, count);
  }

  // Forward from BLEUART to HW Serial
  while (blUART.available()) {
    uint8_t ch;
    ch = (uint8_t) blUART.read();
    Serial.write(ch);
  }

  Serial.print("{ ");

  Serial.print("\"time\": ");
  Serial.print(time);
  Serial.print(", ");

  Serial.print("\"acc_x\": ");
  Serial.print(accel.acceleration.x, 4);
  Serial.print(", ");

  Serial.print("\"acc_y\": ");
  Serial.print(accel.acceleration.y, 4);
  Serial.print(", ");

  Serial.print("\"acc_z\": ");
  Serial.print(accel.acceleration.z, 4);
  Serial.print(", ");

  Serial.print("\"gyro_x\": ");
  Serial.print(gyro.gyro.x, 4);
  Serial.print(", ");

  Serial.print("\"gyro_y\": ");
  Serial.print(gyro.gyro.y, 4);
  Serial.print(", ");

  Serial.print("\"gyro_z\": ");
  Serial.print(gyro.gyro.z, 4);
  Serial.print(", ");

  Serial.print("\"mag_x\": ");
  Serial.print(mag.magnetic.x, 4);
  Serial.print(", ");

  Serial.print("\"mag_y\": ");
  Serial.print(mag.magnetic.y, 4);
  Serial.print(", ");

  Serial.print("\"mag_z\": ");
  Serial.print(mag.magnetic.z, 4);
  Serial.print(", ");

  Serial.print("\"temp\": ");
  Serial.print(temp.temperature);
  Serial.print(" ");

  Serial.println("} ");

  delay(100);

  // // Print acceleration in `m/s^2`
  // Serial.print("\t\tAccel X: ");
  // Serial.print(accel.acceleration.x, 4);
  // Serial.print(" \tY: ");
  // Serial.print(accel.acceleration.y, 4);
  // Serial.print(" \tZ: ");
  // Serial.print(accel.acceleration.z, 4);
  // Serial.println(" \tm/s^2 ");

  // // Print rotation in `rad/s`
  // Serial.print("\t\tGyro  X: ");
  // Serial.print(gyro.gyro.x, 4);
  // Serial.print(" \tY: ");
  // Serial.print(gyro.gyro.y, 4);
  // Serial.print(" \tZ: ");
  // Serial.print(gyro.gyro.z, 4);
  // Serial.println(" \tradians/s ");

  // // Print magnetic field in `uTesla`
  // Serial.print(" \t\tMag   X: ");
  // Serial.print(mag.magnetic.x, 4);
  // Serial.print(" \tY: ");
  // Serial.print(mag.magnetic.y, 4);
  // Serial.print(" \tZ: ");
  // Serial.print(mag.magnetic.z, 4);
  // Serial.println(" \tuTesla ");

  // Serial.print("\t\tTemp   :\t\t\t\t\t");
  // Serial.print(temp.temperature);
  // Serial.println(" \tdeg C");
  // Serial.println();
  // delay(1000);
}
