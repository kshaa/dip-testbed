#![feature(osstring_ascii)]
use clap::{Arg, App};
use log::*;
use url::Url;
use tokio_tungstenite::{
    connect_async,
    tungstenite::{Error, Result},
};

#[tokio::main]
async fn main() {
    let env = env_logger::Env::default();
    let env_with_info_log = env.filter_or(env_logger::DEFAULT_FILTER_ENV, "info");
    env_logger::init_from_env(env_with_info_log);

    let app = App::new("agent")
        .about("Run hardware connectivity agent for DIP testbed")
        .arg(Arg::with_name("server")
            .short("s")
            .long("server")
            .value_name("server")
            .help("URL of DIP testbed server e.g. ws://localhost:9000/agents")
            .takes_value(true)
            .required(true))
        .subcommand(
            App::new("adafruit-nrf52-sh")
                .about("Run shell-script based nRF52 agent")
                .arg(Arg::with_name("baudrate")
                    .short("b")
                    .long("baudrate")
                    .value_name("baudrate")
                    .help("Baudrate of communication over serial port with nRF52 device")
                    .takes_value(true)
                    .required(true))
                .arg(Arg::with_name("device")
                    .short("d")
                    .long("device")
                    .value_name("device")
                    .help("Device serial port e.g. /dev/ttyUSB0")
                    .takes_value(true)
                    .required(true))
        );
    let matches = app.get_matches();
    let url: Url = matches.value_of_t("server").unwrap_or_else(|e| e.exit());

    if let Some(o) = matches.value_of("server") {
        println!("Value for output: {}", o);
    }


    // let (mut socket, _) = connect_async(
    //     Url::parse("ws://localhost:9001/getCaseCount").expect("Can't connect to case count URL"),
    // ).await?;
}
