#ifndef FRISBEE_ENGINE_HPP
#define FRISBEE_ENGINE_HPP

#include <Arduino.h>

typedef bool (*FailableEngineCallback)();
void runUntilSuccess(FailableEngineCallback callback, uint32_t timeout);
void runUntilSuccessSerial(FailableEngineCallback callback, String serviceName, uint32_t timeout);


#endif
