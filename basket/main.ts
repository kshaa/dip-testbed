const noble = require('@abandonware/noble');

console.log("started")
noble.on('stateChange', async (state: any) => {
  console.log(`state change: ${state}`)
  if (state === 'poweredOn') {
    console.log(`powered on, started scanning`)
    await noble.startScanningAsync([], false);
  }
});

noble.on('discover', async (peripheral: any) => {
  console.log(`discovered device: ${peripheral}`)
  await noble.stopScanningAsync();
  await peripheral.connectAsync();
  const {characteristics} = await peripheral.discoverSomeServicesAndCharacteristicsAsync([], []);
  const vertiba = characteristics.find((c: any) => c.uuid == '2a37')
  console.log(vertiba)
  vertiba.on('read', (data: any, isNotification: boolean) => {
    console.log(data, isNotification)
  });
  vertiba.subscribe((error: any) => { console.log(error)})
  const buffer = (await vertiba.readAsync());     
  console.log(buffer.readUInt8(0));
  console.log(buffer.readUInt8(1));

//   await peripheral.disconnectAsync();
//   process.exit(0);
});
