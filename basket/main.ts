const noble = require('@abandonware/noble')

// The proprietary UART profile by Nordic Semiconductor
const uartServiceUuid = '6e400001b5a3f393e0a9e50e24dcca9e'
const uartTxCharacteristicUuid = '6e400002b5a3f393e0a9e50e24dcca9e'
const uartRxCharacteristicUuid = '6e400003b5a3f393e0a9e50e24dcca9e'
const batteryLevelUuid = '2a19'
const frisbeeLocalName = 'IoT Frisbee'
const frisbeeGoalPollIntervalMs = 1000

// Initialize basket
console.log("Running IoT Basket")

// Configure scanner
noble.on('stateChange', async (state: any) => {
  if (state === 'poweredOn') {
    console.log(`powered on, starting scanning`)
    await noble.startScanningAsync([], false)
  } else {
    console.log(`not powered on, stopping scanning`)
    await noble.stopScanning()
  }
});
noble.on('scanStart', function() {
  console.log("Started scanning")
});
noble.on('scanStop', function() {
  console.log('Stopped scanning');
});

// Configure frisbee detector
noble.on('discover', async (peripheral: any) => {
  // Assert that discovered device is a frisbee
  const isFrisbee = peripheral.advertisement.localName.startsWith(frisbeeLocalName)
  if (!isFrisbee) return;

  // Connect to frisbee
  await peripheral.connectAsync()

  // Handle eventual frisbee - basket goal
  const isGoal = await goalCondition(peripheral)
  if (isGoal) {
    // If frisbee is in basket handle goal
    await handleGoal(peripheral)
  } else {
    // If frisbee is not in basket, poll for goal
    const interval = setInterval(() => {
      peripheral.updateRssi(async function() {
        const isGoal = await goalCondition(peripheral)
        if (isGoal) {
          clearInterval(interval)
          await handleGoal(peripheral)
        }
      });
    }, frisbeeGoalPollIntervalMs)
  }
});

async function goalCondition(peripheral: any): Promise<boolean> {
  // Assert that the frisbee is close enough to be considered "in a basket",
  // for this proof-of-concept assume that being very close to the basket
  // i.e. (strong signal) is equivalent to the frisbee being in the basket
  let rssiText = null
  if (peripheral.rssi >= 0) rssiText = "No signal";
  if (peripheral.rssi < 0 && peripheral.rssi >= -50) rssiText = "Excellent";
  if (peripheral.rssi < -50 && peripheral.rssi >= -60) rssiText = "Very good";
  if (peripheral.rssi < -60 && peripheral.rssi >= -70) rssiText = "Good";
  if (peripheral.rssi < -70 && peripheral.rssi >= -80) rssiText = "Low";
  if (peripheral.rssi < -80 && peripheral.rssi <= -90) rssiText = "Very low";
  const rssiHumanReadable = `${peripheral.rssi} (${rssiText})`
  let isInBasket = peripheral.rssi < 0 && peripheral.rssi >= -50

  // Log discovered frisbee status and assert it's in the basket
  console.log(`Device '${peripheral.advertisement.localName}', RSSI: ${rssiHumanReadable}, in basket = ${isInBasket}`)

  return isInBasket
}

async function handleGoal(peripheral: any) {
  // Frisbee is in the basket, connect
  console.log("Frisbee seems to have fallen in the basket, inspecting...")
  const {characteristics} = await peripheral.discoverSomeServicesAndCharacteristicsAsync([], [])
  
  // Assert all communication characteristics are available
  const battery = characteristics.find((c: any) => c.uuid == batteryLevelUuid)
  const tx = characteristics.find((c: any) => c.uuid == uartTxCharacteristicUuid)
  const rx = characteristics.find((c: any) => c.uuid == uartRxCharacteristicUuid)
  if (!(battery && tx && rx)) {
    console.log("Failed to establish communication w/ frisbee: 'battery', 'rx' or 'tx' not available")
    return
  }

  // Create communication channel
  extractFrisbeeData(peripheral, battery, rx, tx)
}

// Configure established connection handler
function extractFrisbeeData(frisbee: any, battery: any, rx: any, tx: any) {
  console.log("Frisbee UART connection found, extracting data")
  
  rx.notify(true)
  rx.on('data', function(data: any) {
    console.log('Data: ', data.toString());
  })
}