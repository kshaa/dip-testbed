# Bluetooth

## Concepts
- `SIG` - Bluetooth Special Interest Group  
- `Bluetooth (Classic Bluetooth)` - Self-explanatory, introduced @ 1989
- `Bluetooth (BLE)` - Bluetooth Low Energy, introduced @ 2009 (part of Bluetooth spec v4 and up)
- `ATT` - Bluetooth ATTribute protocol  
- `GATT` - Bluetooth Generic ATTribute protocol (uses ATT underneath)  
- `GAP` - Generic Access Profile `Profile = { List<Service> = { List<Characteristic> = ... } }` i.e. device profile, e.g. Heart Rate Monitor's profile  
- `Service` - Groups of conceptually related user data called characteristics e.g. Heart Rate Service
- `Characteristic` - A piece of read/write user data 
- `Beacon` - 

Bluetooth devices use server/client communication:  
- `Client` - a central device (i.e. iPhone, Android, PC, Linux, etc.), which sends requests/inquiries  
- `Server` - a peripheral device (i.e. Heart rate monitor, speaker, headphones, etc. ), which receives requests  

Example:
- `Android (client)` connects to `BT headphones (server)` using GATT (ATT underneath)  
- Over the `GATT` connection either the client or server initiates `pairing` and they establish a [`bond`](https://developer.android.com/reference/android/bluetooth/BluetoothDevice#createBond()) (i.e. they are paired)  
- The headphones emit information about the services they provide and the characteristics of those services
- Android then interacts w/ these services & their characteristics

_Note: Bluetooth is extremely broad, see `List of Bluetooth protocols` below. I'm just interested in any data being transferred, I don't care how. Also there are multiple versions and variations of Bluetooth, not everything is relevant or necessarily related, some things seem ignorable._  

## Literature
- [Adafruit BLE introduction](https://learn.adafruit.com/introduction-to-bluetooth-low-energy/)  
- [Bluetooth versions and features](https://en.wikipedia.org/wiki/Bluetooth#Specifications_and_features)  
- [SIG-assigned 16-bit UUIDs](https://btprodspecificationrefs.blob.core.windows.net/assigned-values/16-bit%20UUID%20Numbers%20Document.pdf)  
- [Official specification GAPs i.e. peripheral profiles (I think you can build custom ones though)](https://www.bluetooth.com/specifications/specs/)  
- [Bluetooth GATT protocol](https://www.oreilly.com/library/view/getting-started-with/9781491900550/ch04.html)  
- [List of Bluetooth protocols](https://en.wikipedia.org/wiki/List_of_Bluetooth_protocols#Low_Energy_Attribute_Protocol_(ATT))  

## Tech
- `let adapters = manager.adapters().unwrap()` - [AdapterManager i.e. Available bluetooth adapters](https://docs.rs/btleplug/0.7.2/btleplug/api/struct.AdapterManager.html)  
- `let central = adapters.into_iter().nth(0).unwrap();` - [`Adapter` i.e. Client/central device](https://docs.rs/blurz/0.4.0/blurz/bluetooth_device/struct.BluetoothDevice.html)  
- `let devices = central.peripherals()` - [`Peripheral` i.e. Server/peripheral device](https://docs.rs/btleplug/0.7.2/btleplug/api/trait.Peripheral.html)  
- `let properties = device.properties()` - `PeripheralProperties` i.e. adress, manufacturer, power level, available services  
- `let characteristics = device.characteristics()` - [Characteristics](https://docs.rs/btleplug/0.7.2/btleplug/api/struct.Characteristic.html)  

_Note: [It seems](https://github.com/deviceplug/btleplug/issues/11) that currently `btleplug` doesn't care much about services,
because everything one might want to do w/ Bluetooth can be done w/ just the characteristics themselves, because services are just groupings._

### Adapter
```rust
/// Adapter represents a physical bluetooth interface in your system, for example a bluetooth
/// dongle.
#[derive(Clone)]
pub struct Adapter {
    connection: Arc<SyncConnection>,
    listener: Arc<ReentrantMutex<SyncConnection>>,
    path: String,
    manager: AdapterManager<Peripheral>,
    match_tokens: Arc<DashMap<TokenType, Token>>,

    should_stop: Arc<(Condvar, Mutex<bool>)>,
    thread_handle: Arc<Mutex<Option<JoinHandle<()>>>>,
}
```

### Peripheral
```rust
/// Peripheral is the device that you would like to communicate with (the "server" of BLE). This
/// struct contains both the current state of the device (its properties, characteristics, etc.)
/// as well as functions for communication.
pub trait Peripheral: Send + Sync + Clone + Debug {
    /// Returns the address of the peripheral.
    fn address(&self) -> BDAddr;

    /// Returns the set of properties associated with the peripheral. These may be updated over time
    /// as additional advertising reports are received.
    fn properties(&self) -> PeripheralProperties;

    /// The set of characteristics we've discovered for this device. This will be empty until
    /// `discover_characteristics` is called.
    fn characteristics(&self) -> BTreeSet<Characteristic>;

    /// Returns true iff we are currently connected to the device.
    fn is_connected(&self) -> bool;

    /// Creates a connection to the device. This is a synchronous operation; if this method returns
    /// Ok there has been successful connection. Note that peripherals allow only one connection at
    /// a time. Operations that attempt to communicate with a device will fail until it is connected.
    fn connect(&self) -> Result<()>;

    /// Terminates a connection to the device. This is a synchronous operation.
    fn disconnect(&self) -> Result<()>;

    /// Discovers all characteristics for the device. This is a synchronous operation.
    fn discover_characteristics(&self) -> Result<Vec<Characteristic>>;

    /// Write some data to the characteristic. Returns an error if the write couldn't be send or (in
    /// the case of a write-with-response) if the device returns an error.
    fn write(
        &self,
        characteristic: &Characteristic,
        data: &[u8],
        write_type: WriteType,
    ) -> Result<()>;

    /// Sends a request (read) to the device. Synchronously returns either an error if the request
    /// was not accepted or the response from the device.
    fn read(&self, characteristic: &Characteristic) -> Result<Vec<u8>>;

    /// Sends a read-by-type request to device for the range of handles covered by the
    /// characteristic and for the specified declaration UUID. See
    /// [here](https://www.bluetooth.com/specifications/gatt/declarations) for valid UUIDs.
    /// Synchronously returns either an error or the device response.
    fn read_by_type(&self, characteristic: &Characteristic, uuid: Uuid) -> Result<Vec<u8>>;

    /// Enables either notify or indicate (depending on support) for the specified characteristic.
    /// This is a synchronous call.
    fn subscribe(&self, characteristic: &Characteristic) -> Result<()>;

    /// Disables either notify or indicate (depending on support) for the specified characteristic.
    /// This is a synchronous call.
    fn unsubscribe(&self, characteristic: &Characteristic) -> Result<()>;

    /// Registers a handler that will be called when value notification messages are received from
    /// the device. This method should only be used after a connection has been established. Note
    /// that the handler will be called in a common thread, so it should not block.
    fn on_notification(&self, handler: NotificationHandler);
}
```

### PeripheralProperties
```rust
/// The properties of this peripheral, as determined by the advertising reports we've received for
/// it.
#[derive(Debug, Default, Clone)]
pub struct PeripheralProperties {
    /// The address of this peripheral
    pub address: BDAddr,
    /// The type of address (either random or public)
    pub address_type: AddressType,
    /// The local name. This is generally a human-readable string that identifies the type of device.
    pub local_name: Option<String>,
    /// The transmission power level for the device
    pub tx_power_level: Option<i8>,
    /// Advertisement data specific to the device manufacturer. The keys of this map are
    /// 'manufacturer IDs', while the values are arbitrary data.
    pub manufacturer_data: HashMap<u16, Vec<u8>>,
    /// Advertisement data specific to a service. The keys of this map are
    /// 'Service UUIDs', while the values are arbitrary data.
    pub service_data: HashMap<Uuid, Vec<u8>>,
    /// Advertised services for this device
    pub services: Vec<Uuid>,
    /// Number of times we've seen advertising reports for this device
    pub discovery_count: u32,
    /// True if we've discovered the device before
    pub has_scan_response: bool,
}
```
