#include <Arduino.h>
#include "frisbee_engine.hpp"

void runUntilSuccessSerializable(FailableEngineCallback callback, uint32_t timeout, String initText, String endText, bool enablePrint) {
  if (enablePrint) Serial.print(initText);
  bool success = callback();
  while (!success) {
    delay(timeout);
    if (enablePrint) Serial.print(".");
    success = callback();
  }
  if (enablePrint) Serial.println();
  if (enablePrint) Serial.println(endText);
}

void runUntilSuccess(FailableEngineCallback callback, uint32_t timeout) {
  runUntilSuccessSerializable(callback, timeout, "", "", false);
}

void runUntilSuccessSerial(FailableEngineCallback callback, String serviceName, uint32_t timeout) {
  String initText = "Starting " + serviceName;
  String endText = "Started " + serviceName;
  runUntilSuccessSerializable(callback, timeout, initText, endText, true);
}