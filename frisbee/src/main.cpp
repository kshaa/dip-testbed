#include <Arduino.h>
#include <Adafruit_LSM6DSOX.h>
#include <Adafruit_LIS3MDL.h>
#include "frisbee_config.h"
#include "lsm6ds_sensor.h"
#include "lis3mdl_sensor.h"

Adafruit_LSM6DSOX lsm6ds;
Adafruit_LIS3MDL lis3mdl;

void setup(void) {
  // Initialize and wait for serial port
  Serial.begin(ADA_NRF52_BAUD_RATE);
  while (!Serial) delay(SERIAL_TIMEOUT_MS);
  Serial.println("Initializing iot-frisbee with Adafruit nRF52, LSM6DS, LIS3MDL!");

  // Initiate communication w/ LSM6DS sensor over I2C
  Serial.print("Initializing I2C connection with LSM6DS chip");
  bool lsm6ds_success = lsm6ds.begin_I2C();
  while (!lsm6ds_success) {
    Serial.print(".");
    delay(LSM6DS_TIMEOUT_MS);
    lsm6ds_success = lsm6ds.begin_I2C();
  }
  Serial.println();
  Serial.println("Communications with LSM6DS chip established");

  // Initiate communication w/ LIS3MDL sensor over I2C
  Serial.print("Initializing I2C connection with LIS3MDL chip");
  bool lis3mdl_success = lis3mdl.begin_I2C();
  while (!lis3mdl_success) {
    Serial.print(".");
    delay(LIS3MDL_TIMEOUT_MS);
    lis3mdl_success = lis3mdl.begin_I2C();
  }
  Serial.println();
  Serial.println("Communications with LIS3MDL chip established");

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
}

void loop() {
  // Read sensor values
  sensors_event_t accel, gyro, mag, temp;
  bool lsm6ds_success = lsm6ds.getEvent(&accel, &gyro, &temp);
  bool lis3mdl_success = lis3mdl.getEvent(&mag);

  // Print acceleration in `m/s^2`
  Serial.print("\t\tAccel X: ");
  Serial.print(accel.acceleration.x, 4);
  Serial.print(" \tY: ");
  Serial.print(accel.acceleration.y, 4);
  Serial.print(" \tZ: ");
  Serial.print(accel.acceleration.z, 4);
  Serial.println(" \tm/s^2 ");

  // Print rotation in `rad/s`
  Serial.print("\t\tGyro  X: ");
  Serial.print(gyro.gyro.x, 4);
  Serial.print(" \tY: ");
  Serial.print(gyro.gyro.y, 4);
  Serial.print(" \tZ: ");
  Serial.print(gyro.gyro.z, 4);
  Serial.println(" \tradians/s ");

  // Print magnetic field in `uTesla`
  Serial.print(" \t\tMag   X: ");
  Serial.print(mag.magnetic.x, 4);
  Serial.print(" \tY: ");
  Serial.print(mag.magnetic.y, 4);
  Serial.print(" \tZ: ");
  Serial.print(mag.magnetic.z, 4);
  Serial.println(" \tuTesla ");

  Serial.print("\t\tTemp   :\t\t\t\t\t");
  Serial.print(temp.temperature);
  Serial.println(" \tdeg C");
  Serial.println();
  delay(1000);
}
