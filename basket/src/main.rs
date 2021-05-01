// Basket gateway
mod gateway;
use gateway::api::Gateway;
use gateway::tcp_gateway::TCPGateway;

// Bluetooth adapter & manager
#[cfg(target_os = "linux")]
use btleplug::bluez::{adapter::Adapter, manager::Manager};
#[cfg(target_os = "windows")]
use btleplug::winrtble::{adapter::Adapter, manager::Manager};
#[cfg(target_os = "macos")]
use btleplug::corebluetooth::{adapter::Adapter, manager::Manager};

// Miscellaneous
use std::thread;
use std::time::Duration;
use rand::{Rng, thread_rng};

use btleplug::api::{bleuuid::uuid_from_u16, CentralEvent, CharPropFlags, Central, Peripheral, Characteristic, WriteType};
use std::collections::{BTreeSet};

// use btleplug::api::{bleuuid::uuid_from_u16, Central, Manager as _, Peripheral as _, WriteType};
// use btleplug::platform::{Adapter, Manager, Peripheral};
// use rand::{thread_rng, Rng};
// use std::error::Error;
// use std::time::Duration;
// use uuid::Uuid;


const LIGHT_CHARACTERISTIC_UUID: uuid::Uuid = uuid_from_u16(0xFFE9);

pub fn main() {
    // Initialize message gateway
    let gateway = TCPGateway::init("127.0.0.1".to_owned(), 3000);

    // Get the first bluetooth adapter
    let manager = Manager::new().expect("Could not initialize bluetooth driver");
    let adapters: Vec<Adapter> = manager.adapters().expect("Could not list bluetooth adapters");
    let central = adapters.into_iter().nth(0).expect("No bluetooth adapters seem to be available");
    
    // Scan for devices for 2 seconds & print them all
    central.start_scan().expect("Could not start bluetooth scanner");
    thread::sleep(Duration::from_secs(2));
    let devices = central.peripherals();
    for device in devices.iter() {
        // Assert available device name
        let device_name = match device.properties().local_name {
            None => format!("Unnamed"), // continue,
            Some(name) => name,
        };

        // Send device name to gateway
        gateway
            .send(format!("Device: {}\n", device_name).as_bytes())
            .map(|err| println!("Error sending bluetooth local device to gateway: {}", err));

        // Send device services to gateway
        println!("{} has {} services", device_name, device.properties().services.len());
        for service in device.properties().services.iter() {
            gateway
                .send(format!("Service: {}\n", service).as_bytes())
                .map(|err| println!("Error sending bluetooth local device to gateway: {}", err));
        }

        // Assert available device characteristics
        let chars: Vec<Characteristic> = match device.discover_characteristics() {
            Err(err) => { println!("Failed to read {} characteristics: {}", device_name, err); continue },
            Ok(chars) => { println!("{} has {} or {} characteristics", device_name, chars.len(), device.characteristics().len() ); chars},
        };

        // Send device characteristics to gateway
        for char in chars.iter() {
            let propchart = format!(
                "b:{},r:{},w:{},wr:{},n:{},i:{},a:{},e:{}",
                char.properties.contains(CharPropFlags::BROADCAST),
                char.properties.contains(CharPropFlags::READ),
                char.properties.contains(CharPropFlags::WRITE_WITHOUT_RESPONSE),
                char.properties.contains(CharPropFlags::WRITE),
                char.properties.contains(CharPropFlags::NOTIFY),
                char.properties.contains(CharPropFlags::INDICATE),
                char.properties.contains(CharPropFlags::AUTHENTICATED_SIGNED_WRITES),
                char.properties.contains(CharPropFlags::EXTENDED_PROPERTIES),
            );

            gateway
                .send(format!("Characteristic[{}]: {}\n", char.uuid, propchart).as_bytes())
                .map(|err| println!("Error sending bluetooth local device to gateway: {}", err));
        }
    }

    // // find the device we're interested in
    // let light = central.peripherals().into_iter()
    //     .find(|p| p.properties().local_name.iter()
    //         .any(|name| name.contains("LEDBlue"))).unwrap();

    // // connect to the device
    // light.connect().unwrap();

    // // discover characteristics
    // light.discover_characteristics().unwrap();

    // // find the characteristic we want
    // let chars: BTreeSet<Characteristic> = light.characteristics();
    // let cmd_char = chars.iter().find(|c| c.uuid == LIGHT_CHARACTERISTIC_UUID).unwrap();

    // // dance party
    // let mut rng = thread_rng();
    // for _ in 0..20 {
    //     let color_cmd = vec![0x56, rng.gen(), rng.gen(), rng.gen(), 0x00, 0xF0, 0xAA];
    //     light.write(&cmd_char, &color_cmd, WriteType::WithoutResponse).unwrap();
    //     thread::sleep(Duration::from_millis(200));
    // }
}
