#ifndef LSM6DS_SENSOR_HPP
#define LSM6DS_SENSOR_HPP

#include <Adafruit_LSM6DSOX.h>

char * lsm6dsAccelRangeText(lsm6ds_accel_range_t rangeValue);
char * lsm6dsGyroRangeText(lsm6ds_gyro_range_t gyroRangeValue);
char * lsm6dsDataRateText(lsm6ds_data_rate_t dataRateValue);

#endif
