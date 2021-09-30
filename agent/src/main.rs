use std::path::PathBuf;
use log::*;
use url::Url;
// use std::fs::File;
use std::result;
use std::str;
use futures_util::{stream, future, pin_mut, Sink, SinkExt, StreamExt};
use std::clone::Clone;
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
use commands::*;
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
        let (ws_tx, ws_rx) = futures_channel::mpsc::unbounded::<Message>();
        info!("Successful server connection & message channel creation");

        // Connect to stdio
        debug!("Connecting stdio");
        let (stdin_tx, stdin_rx) = futures_channel::mpsc::unbounded();
        let stdin_tx_handle = tokio::spawn(read_stdin(stdin_tx));
        info!("Successful stdio connection & message channel creation");

        // Connect stdio and agent logic to server
        debug!("Attaching agent logic to server");
        let (mut sink, stream) = ws_stream.split();
        let other_to_ws = ws_rx.map(Ok).forward(&mut sink);

        let ws_to_stdout = stream.for_each(|message| async {
            let data = message.unwrap().into_data();
            let utf8_data: &str = match str::from_utf8(&data) {
                Ok(it) => it,
                Err(err) => {
                    let info: String = format!("Invalid UTF-8 sequence: {}", err);
                    debug!("{}", info);
                    let parse_message = OutgoingMessage::ParseMessage(ParseMessage { info });
                    let serialized = match serde_json::to_string(&parse_message) {
                        Ok(it) => it,
                        Err(err) => {
                            error!("Failed to construct message about failure to parse UTF-8 message: {}", err);
                            return;
                        }
                    };
                    let response_message: Message = Message::Text(serialized);
                    match ws_tx.unbounded_send(response_message) {
                        Ok(it) => it,
                        Err(err) => {
                            error!("Failed to send message about failure to parse UTF-8 message: {}", err);
                            return;
                        }
                    };
                    return;
                },
            };
        
            let parsed: IncomingMessage = match serde_json::from_str(utf8_data) {
                Ok(it) => it,
                Err(err) => {
                    let info = format!("Request contains unknown message: {}", err); 
                    debug!("{}", info);
                    let parse_message = OutgoingMessage::ParseMessage(ParseMessage { info });
                    let serialized = match serde_json::to_string(&parse_message) {
                        Ok(it) => it,
                        Err(err) => {
                            error!("Failed to construct message about encountering unknown message: {}", err);
                            return;
                        }
                    };
                    let response_message: Message = Message::Text(serialized);
                    match ws_tx.unbounded_send(response_message) {
                        Ok(it) => it,
                        Err(err) => {
                            error!("Failed to send message about failure to parse UTF-8 message: {}", err);
                            return;
                        }
                    };
                    return;
                }
            };

            match parsed {
                IncomingMessage::MonitorMessage(message) => {
                    println!("Monitor")
                },
                IncomingMessage::UploadMessage(message) => {
                    println!("Upload")
                } 
            }

            return;
        });

        pin_mut!(other_to_ws, ws_to_stdout);
        future::select(other_to_ws, ws_to_stdout).await;
    
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
