#include <Adafruit_LIS3MDL.h>
#include "lis3mdl_sensor.hpp"

const char * lis3mdlMagnetRangeText(lis3mdl_range_t rangeValue) {
  switch (rangeValue) {
    case LIS3MDL_RANGE_4_GAUSS: return "+-4 gauss"; break;
    case LIS3MDL_RANGE_8_GAUSS: return "+-8 gauss"; break;
    case LIS3MDL_RANGE_12_GAUSS: return "+-12 gauss"; break;
    case LIS3MDL_RANGE_16_GAUSS: return "+-16 gauss"; break;
    default: return "?? gauss"; break;
  }
}

const char * lis3mdlMagnetPerformanceModeText(lis3mdl_performancemode_t performanceMode) {
  switch (performanceMode) {
    case LIS3MDL_LOWPOWERMODE: return "Low"; break;
    case LIS3MDL_MEDIUMMODE: return "Medium"; break;
    case LIS3MDL_HIGHMODE: return "High"; break;
    case LIS3MDL_ULTRAHIGHMODE: return "Ultra-High"; break;
    default: return "?? mode"; break;
  }
}

const char * lis3mdlMagnetOperationModeText(lis3mdl_operationmode_t operationMode) {
  switch (operationMode) {
    case LIS3MDL_CONTINUOUSMODE: return "Continuous"; break;
    case LIS3MDL_SINGLEMODE: return "Single mode"; break;
    case LIS3MDL_POWERDOWNMODE: return "Power-down"; break;
    default: return "?? mode"; break;
  }
}

const char * lis3mdlDataRateText(lis3mdl_dataRate_t dataRateValue) {
  switch (dataRateValue) {
    case LIS3MDL_DATARATE_0_625_HZ: return "0.625 Hz"; break;
    case LIS3MDL_DATARATE_1_25_HZ: return "1.25 Hz"; break;
    case LIS3MDL_DATARATE_2_5_HZ: return "2.5 Hz"; break;
    case LIS3MDL_DATARATE_5_HZ: return "5 Hz"; break;
    case LIS3MDL_DATARATE_10_HZ: return "10 Hz"; break;
    case LIS3MDL_DATARATE_20_HZ: return "20 Hz"; break;
    case LIS3MDL_DATARATE_40_HZ: return "40 Hz"; break;
    case LIS3MDL_DATARATE_80_HZ: return "80 Hz"; break;
    case LIS3MDL_DATARATE_155_HZ: return "155 Hz"; break;
    case LIS3MDL_DATARATE_300_HZ: return "300 Hz"; break;
    case LIS3MDL_DATARATE_560_HZ: return "560 Hz"; break;
    case LIS3MDL_DATARATE_1000_HZ: return "1000 Hz"; break;
    default: return "?? Hz"; break;
  }
}
