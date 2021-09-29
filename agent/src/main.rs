use std::path::PathBuf;
use log::*;
use url::Url;
// use std::fs::File;
use std::result;
use futures_util::{future, pin_mut, StreamExt};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio_tungstenite::{
    connect_async,
    tungstenite::{
        // Error as TkError,
        // Result as TgResult,
        protocol::Message
    }
};
mod adafruit_nrf52_sh_agent;
mod commands;
mod errors;
mod cli;
use errors::*;
use cli::agent_cli;

#[tokio::main]
async fn main() -> result::Result<(), AgentError> {
    // Setup logging
    let env = env_logger::Env::default();
    let env_with_info_log = env.filter_or(env_logger::DEFAULT_FILTER_ENV, "info");
    env_logger::init_from_env(env_with_info_log);

    // Parse CLI parameters
    let params = agent_cli().get_matches();
    let server: Url = params.value_of_t("server").unwrap_or_else(|e| e.exit());

    // Parse sub-agent parameters
    if let Some(ref subparams) = params.subcommand_matches("adafruit-nrf52-sh") {
        let baudrate: u32 = subparams.value_of_t("baudrate").unwrap_or_else(|e| e.exit());
        let device: PathBuf = subparams.value_of_t("device").unwrap_or_else(|e| e.exit());
        
        if !device.exists() {
            return Err(AgentError::StartupError(StartupError(BasicAgentError::new(
                "Device file does not exist"))))
        }

        info!("Starting nRF52 agent");

        // Connect to server
        info!("Connecting to server '{}'", server);
        let (ws_stream, _) = match connect_async(server).await {
            Ok(it) => it,
            Err(err) => {
                let msg = format!("Failed connecting to the server: {}", err);
                return Err(AgentError::StartupError(StartupError(BasicAgentError::new(&msg.to_string()))))
            }
        };
        info!("Successful connection");

        // Spawn rx/tx connection w/ stdio
        debug!("Connecting stdio");
        let (stdin_tx, stdin_rx) = futures_channel::mpsc::unbounded();
        let stdin_tx_handle = tokio::spawn(read_stdin(stdin_tx));
                
        // Connect stdio to server
        debug!("Attaching stdio to server");
        let (write, read) = ws_stream.split();
        let stdin_to_ws = stdin_rx.map(Ok).forward(write);
        let ws_to_stdout = {
            read.for_each(|message| async {
                let data = message.unwrap().into_data();
                tokio::io::stdout().write_all(&data).await.unwrap();
            })
        };

        pin_mut!(stdin_to_ws, ws_to_stdout);
        future::select(stdin_to_ws, ws_to_stdout).await;
    
        return Ok(())
    } else {
        return Err(AgentError::StartupError(StartupError(BasicAgentError::new(
            "Subcommand for agent is required"))))
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
