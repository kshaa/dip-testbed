#ifndef LIS3MDL_SENSOR_H
#define LIS3MDL_SENSOR_H

#include "Adafruit_LIS3MDL.h"

char * lis3mdlMagnetRangeText(lis3mdl_range_t rangeValue);
char * lis3mdlMagnetPerformanceModeText(lis3mdl_performancemode_t performanceMode);
char * lis3mdlMagnetOperationModeText(lis3mdl_operationmode_t operationMode);
char * lis3mdlDataRateText(lis3mdl_dataRate_t dataRateValue);

#endif
