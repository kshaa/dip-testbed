#ifndef FRISBEE_CONFIG_HPP
#define FRISBEE_CONFIG_HPP

#include "bluefruit.h"
#include "Adafruit_LSM6DSOX.h"
#include "Adafruit_LIS3MDL.h"

// Generic Adafruit/Arduino configurations
const unsigned long ADA_NRF52_BAUD_RATE = 115200;
const uint32_t SERVICE_INIT_TIMEOUT_MS = 50;

// LSM6DS sensor configurations
const lsm6ds_accel_range_t LSM6DS_ACCEL_RANGE = LSM6DS_ACCEL_RANGE_4_G;
const lsm6ds_data_rate_t LSM6DS_ACCEL_DATA_RATE = LSM6DS_RATE_12_5_HZ;
const lsm6ds_gyro_range_t LSM6DS_GYRO_RANGE = LSM6DS_GYRO_RANGE_250_DPS;
const lsm6ds_data_rate_t LSM6DS_GYRO_DATA_RATE = LSM6DS_RATE_12_5_HZ;

// LIS3MDL sensor configurations
const lis3mdl_dataRate_t LIS3MDL_MAGNET_DATA_RATE = LIS3MDL_DATARATE_155_HZ;
const lis3mdl_range_t LIS3MDL_MAGNET_RANGE = LIS3MDL_RANGE_4_GAUSS;
const lis3mdl_performancemode_t LIS3MDL_PERFORMANCE_MODE = LIS3MDL_MEDIUMMODE;
const lis3mdl_operationmode_t LIS3MDL_OPERATION_MODE = LIS3MDL_CONTINUOUSMODE;
const uint16_t LIS3MDL_INT_TRESHOLD = 500;
const bool LIS3MDL_ENABLE_X = false;
const bool LIS3MDL_ENABLE_Y = false;
const bool LIS3MDL_ENABLE_Z = true;
const bool LIS3MDL_ENABLE_POLARITY = true;
const bool LIS3MDL_ENABLE_LATCH = false;
const bool LIS3MDL_ENABLE_INTERRUPTS = true;

// Bluetooth configurations
bool BL_AUTO_CONN_LED = false;
char BL_DEVICE_NAME[] = "IoT Frisbee";
char BL_DEVICE_MANUFACTURER[] = "Adafruit Industries";
char BL_DEVICE_MODEL[] = "Bluefruit Feather52";
uint8_t BL_ADVERTISEMENT_FLAGS = BLE_GAP_ADV_FLAGS_LE_ONLY_GENERAL_DISC_MODE;
bool BL_READVERTISE_ON_DISCONNECT = true;
bool BL_FAST_RETRY_INTERVAL_MS = 32;
bool BL_FAST_TIMEOUT_S = 30;
bool BL_SLOW_RETRY_INTERVAL_MS = 244;

#endif
