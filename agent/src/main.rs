use clap::{Arg, App};
use std::path::PathBuf;
use std::process;
use log::*;
use url::Url;
// use std::fs::File;
use std::error;
use std::fmt;
use std::result;
use futures_util::{future, pin_mut, StreamExt};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio_tungstenite::{
    connect_async,
    tungstenite,
    tungstenite::{
        // Error as TkError,
        // Result as TgResult,
        protocol::Message
    }
};

#[derive(Debug)]
struct StringError {
    details: String
}

impl StringError {
    fn new(msg: &str) -> StringError {
        StringError { details: msg.to_string() }
    }
}

impl fmt::Display for StringError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.details)
    }
}

impl error::Error for StringError {
    fn description(&self) -> &str {
        &self.details
    }
}

#[tokio::main]
async fn main() -> result::Result<(), StringError> {
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
            return Err(StringError::new("error: Device file does not exist"))
        }

        info!("Starting nRF52 agent");

        // Spawn rx/tx connection w/ stdio
        // debug!("Initiating stdio connection");
        // let (stdin_tx, stdin_rx) = futures_channel::mpsc::unbounded();
        // let stdin_tx_handle = tokio::spawn(read_stdin(stdin_tx));

        // Connect to server
        info!("Connecting to server '{}'", server);
        let connection = match (connect_async(server).await) {
            Ok(it) => it,
            Err(err) => return Err(StringError::new(&err.to_string()))
        };
        info!("Successful connection");

        return Ok(())
    } else {
        return Err(StringError::new("Subcommand for agent is required"));
    }
}

// Our helper method which will read data from stdin and send it along the
// sender provided.
async fn read_stdin(tx: futures_channel::mpsc::UnboundedSender<Message>) {
    let mut stdin = tokio::io::stdin();
    loop {
        let mut buf = vec![0; 1024];
        let n = match stdin.read(&mut buf).await {
            Err(_) | Ok(0) => break,
            Ok(n) => n,
        };
        buf.truncate(n);
        tx.unbounded_send(Message::binary(buf)).unwrap();
    }
}
