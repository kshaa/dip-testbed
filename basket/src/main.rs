// use std::thread;
// use std::time::Duration;
// use rand::{Rng, thread_rng};
// #[cfg(target_os = "linux")]
// use btleplug::bluez::{adapter::Adapter, manager::Manager};
// #[cfg(target_os = "windows")]
// use btleplug::winrtble::{adapter::Adapter, manager::Manager};
// #[cfg(target_os = "macos")]
// use btleplug::corebluetooth::{adapter::Adapter, manager::Manager};
// use btleplug::api::{bleuuid::uuid_from_u16, Central, Peripheral, WriteType};
// use uuid::Uuid;

// const LIGHT_CHARACTERISTIC_UUID: Uuid = uuid_from_u16(0xFFE9);

// adapter retreival works differently depending on your platform right now.
// API needs to be aligned.

mod gateway;
use gateway::api::Gateway;
use gateway::tcp_gateway::TCPGateway;

pub fn main() {
    // let manager = Manager::new().unwrap();

    // // get the first bluetooth adapter
    // let adapters: Vec<Adapter> = manager.adapters().unwrap();
    // let central = adapters.into_iter().nth(0).unwrap();
    
    // // start scanning for devices
    // central.start_scan().unwrap();
    // // instead of waiting, you can use central.event_receiver() to fetch a channel and
    // // be notified of new devices
    // thread::sleep(Duration::from_secs(2));

    // // // Print all devices
    // // let devices = central.peripherals();
    // // for device in devices.iter() {
    // //     println!("{}", device.properties().local_name.unwrap());
    // // }

    // // find the device we're interested in
    // let light = central.peripherals().into_iter()
    //     .find(|p| p.properties().local_name.iter()
    //         .any(|name| name.contains("LEDBlue"))).unwrap();

    // // connect to the device
    // light.connect().unwrap();

    // // discover characteristics
    // light.discover_characteristics().unwrap();

    // // find the characteristic we want
    // let chars: Vec<Characteristic> = light.characteristics();
    // let cmd_char = chars.iter().find(|c| c.uuid == LIGHT_CHARACTERISTIC_UUID).unwrap();

    // // dance party
    // let mut rng = thread_rng();
    // for _ in 0..20 {
    //     let color_cmd = vec![0x56, rng.gen(), rng.gen(), rng.gen(), 0x00, 0xF0, 0xAA];
    //     light.write(&cmd_char, &color_cmd, WriteType::WithoutResponse).unwrap();
    //     thread::sleep(Duration::from_millis(200));
    // }

    let gateway = TCPGateway::init("127.0.0.1".to_owned(), 3000);
    gateway.send("Yeet".as_bytes()).map(|err| println!("Error sending msg no. 1: {}", err));
    gateway.send("Maybe".as_bytes()).map(|err| println!("Error sending msg no. 1: {}", err));

    return ();
}
