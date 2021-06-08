#ifndef FRISBEE_CONFIG_H
#define FRISBEE_CONFIG_H

#include "Adafruit_LSM6DSOX.h"
#include "Adafruit_LIS3MDL.h"

const unsigned long ADA_NRF52_BAUD_RATE = 115200;
const uint32_t SERIAL_TIMEOUT_MS = 50;
const uint32_t LSM6DS_TIMEOUT_MS = 50;
const uint32_t LIS3MDL_TIMEOUT_MS = 50;

const lsm6ds_accel_range_t LSM6DS_ACCEL_RANGE = LSM6DS_ACCEL_RANGE_4_G;
const lsm6ds_data_rate_t LSM6DS_ACCEL_DATA_RATE = LSM6DS_RATE_12_5_HZ;
const lsm6ds_gyro_range_t LSM6DS_GYRO_RANGE = LSM6DS_GYRO_RANGE_250_DPS;
const lsm6ds_data_rate_t LSM6DS_GYRO_DATA_RATE = LSM6DS_RATE_12_5_HZ;

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

#endif
