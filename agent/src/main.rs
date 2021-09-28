use clap::{Arg, App};
use std::path::PathBuf;
use std::process;
use log::*;
use url::Url;
use std::fs::File;
use tokio_tungstenite::{
    connect_async,
    tungstenite::{Error, Result},
};

#[tokio::main]
async fn main() {
    // Setup logging
    let env = env_logger::Env::default();
    let env_with_info_log = env.filter_or(env_logger::DEFAULT_FILTER_ENV, "info");
    env_logger::init_from_env(env_with_info_log);

    // Define nRF52 agent
    let adafruit_nrf52_sh_agent = App::new("adafruit-nrf52-sh")
        .about("Run shell-script based nRF52 agent")
        .arg(Arg::new("baudrate")
            .short('b')
            .long("baudrate")
            .value_name("baudrate")
            .about("Baudrate of communication over serial port with nRF52 device")
            .takes_value(true)
            .default_value("11520"))
        .arg(Arg::new("device")
            .short('d')
            .long("device")
            .value_name("device")
            .about("Device serial port e.g. /dev/ttyUSB0")
            .takes_value(true)
            .required(true));

    // Define whole agent
    let agent = App::new("agent")
        .about("Run hardware connectivity agent for DIP testbed")
        .arg(Arg::new("server")
            .short('s')
            .long("server")
            .value_name("server")
            .about("URL of DIP testbed server e.g. ws://localhost:9000/agents")
            .takes_value(true)
            .required(true))
        .subcommand(adafruit_nrf52_sh_agent);

    // Parse whole agent parameters
    let params = agent.get_matches();
    let server: Url = params.value_of_t("server").unwrap_or_else(|e| e.exit());

    // Parse sub-agent parameters
    if let Some(ref subparams) = params.subcommand_matches("adafruit-nrf52-sh") {
        let baudrate: u32 = subparams.value_of_t("baudrate").unwrap_or_else(|e| e.exit());
        let device: PathBuf = subparams.value_of_t("device").unwrap_or_else(|e| e.exit());
        if !device.exists() {
            println!("error: Device file does not exist");
            process::exit(1);
        }

        println!("{:?}, {:?}, {:?}", server, baudrate, device);
    } else {
        println!("error: Subcommand for agent is required");
        process::exit(1);
    }
}
