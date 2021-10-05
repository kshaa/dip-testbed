use clap::{Arg, App};

pub fn agent_cli() -> App<'static> {
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
    let agent: App = App::new("agent")
        .about("Run hardware connectivity agent for DIP testbed")
        .arg(Arg::new("control_server")
            .short('c')
            .long("control_server")
            .value_name("control_server")
            .about("URL of DIP testbed control server e.g. ws://localhost:9000/")
            .takes_value(true)
            .required(true))
        .arg(Arg::new("monitor_server")
            .short('m')
            .long("monitor_server")
            .value_name("monitor_server")
            .about("URL of DIP testbed monitor server e.g. ws://localhost:9001/")
            .takes_value(true)
            .required(true))
        .arg(Arg::new("static_server")
            .short('s')
            .long("static_server")
            .value_name("static_server")
            .about("URL of DIP testbed static server e.g. http://localhost:9000/")
            .takes_value(true)
            .required(true))
        .arg(Arg::new("persistence_directory")
            .short('p')
            .long("persistence_directory")
            .value_name("persistence_directory")
            .about("Directory for storing any data - runtime scripts, experiment binaries, log files")
            .takes_value(true)
            .required(true))
        .subcommand(adafruit_nrf52_sh_agent);

    agent
}