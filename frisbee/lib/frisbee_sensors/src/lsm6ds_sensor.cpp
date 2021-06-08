#include "Adafruit_LSM6DSOX.h"
#include "lsm6ds_sensor.h"

char * lsm6dsAccelRangeText(lsm6ds_accel_range_t rangeValue) {
  switch (rangeValue) {
    case LSM6DS_ACCEL_RANGE_2_G:
      return "+-2G";
      break;
    case LSM6DS_ACCEL_RANGE_4_G:
      return "+-4G";
      break;
    case LSM6DS_ACCEL_RANGE_8_G:
      return "+-8G";
      break;
    case LSM6DS_ACCEL_RANGE_16_G:
      return "+-16G";
      break;
    default:
      return "+-??G";
      break;
  }
}

char * lsm6dsGyroRangeText(lsm6ds_gyro_range_t gyroRangeValue) {
  switch (gyroRangeValue) {
    case LSM6DS_GYRO_RANGE_125_DPS:
      return "125 degrees/s";
      break;
    case LSM6DS_GYRO_RANGE_250_DPS:
      return "250 degrees/s";
      break;
    case LSM6DS_GYRO_RANGE_500_DPS:
      return "500 degrees/s";
      break;
    case LSM6DS_GYRO_RANGE_1000_DPS:
      return "1000 degrees/s";
      break;
    case LSM6DS_GYRO_RANGE_2000_DPS:
      return "2000 degrees/s";
      break;
    case ISM330DHCX_GYRO_RANGE_4000_DPS:
      return "4000 degrees/s";
      break;
    default:
      return "? degrees/s";
      break;
  }
}


char * lsm6dsDataRateText(lsm6ds_data_rate_t dataRateValue) {
  switch (dataRateValue) {
    case LSM6DS_RATE_SHUTDOWN:
      return "0 Hz";
      break;
    case LSM6DS_RATE_12_5_HZ:
      return "12.5 Hz";
      break;
    case LSM6DS_RATE_26_HZ:
      return "26 Hz";
      break;
    case LSM6DS_RATE_52_HZ:
      return "52 Hz";
      break;
    case LSM6DS_RATE_104_HZ:
      return "104 Hz";
      break;
    case LSM6DS_RATE_208_HZ:
      return "208 Hz";
      break;
    case LSM6DS_RATE_416_HZ:
      return "416 Hz";
      break;
    case LSM6DS_RATE_833_HZ:
      return "833 Hz";
      break;
    case LSM6DS_RATE_1_66K_HZ:
      return "1.66 KHz";
      break;
    case LSM6DS_RATE_3_33K_HZ:
      return "3.33 KHz";
      break;
    case LSM6DS_RATE_6_66K_HZ:
      return "6.66 KHz";
      break;
    default:
      return "?? Hz";
      break;
  }
}