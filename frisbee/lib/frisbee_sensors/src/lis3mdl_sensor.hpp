#ifndef LIS3MDL_SENSOR_HPP
#define LIS3MDL_SENSOR_HPP

#include <Adafruit_LIS3MDL.h>

const char * lis3mdlMagnetRangeText(lis3mdl_range_t rangeValue);
const char * lis3mdlMagnetPerformanceModeText(lis3mdl_performancemode_t performanceMode);
const char * lis3mdlMagnetOperationModeText(lis3mdl_operationmode_t operationMode);
const char * lis3mdlDataRateText(lis3mdl_dataRate_t dataRateValue);

#endif
