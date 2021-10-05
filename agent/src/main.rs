use core::time::Duration;
use std::time::{SystemTime, UNIX_EPOCH};
use std::path::PathBuf;
use log::*;
use url::Url;
// use std::fs::File;
use std::result;
use std::str;
use futures_channel::mpsc::{UnboundedSender, unbounded};
use futures_util::{future, pin_mut, StreamExt};
use tokio::process::Child;
use tokio::io::AsyncReadExt;
use tokio::task::JoinHandle;
use tokio::time::sleep;
use tokio_tungstenite::{
    connect_async,
    tungstenite::{
        // Error as TgError,
        // Result as TgResult,
        protocol::Message
    }
};
use uuid::Uuid;
mod adafruit_nrf52_sh_agent;
mod commands;
mod errors;
mod cli;
use commands::*;
use errors::*;
use cli::agent_cli;
use std::sync::{Arc, Mutex};
use std::borrow::Borrow;

#[tokio::main]
async fn main() -> result::Result<(), AgentError> {
    // Setup logging
    let env = env_logger::Env::default();
    let env_with_info_log = env.filter_or(env_logger::DEFAULT_FILTER_ENV, "info");
    env_logger::init_from_env(env_with_info_log);

    // Parse CLI parameters
    let params = agent_cli().get_matches();
    let monitor_server: Box<Url> = Box::new(params.value_of_t("monitor_server").unwrap_or_else(|e| e.exit()));
    let control_server: Url = params.value_of_t("control_server").unwrap_or_else(|e| e.exit());
    let static_server: Url = params.value_of_t("static_server").unwrap_or_else(|e| e.exit());
    let persistence_directory: PathBuf = params.value_of_t("persistence_directory").unwrap_or_else(|e| e.exit());

    // Assert agent is defined
    if params.subcommand().is_none() {
        return Err(AgentError::StartupError(StartupError(BasicAgentError::new(
            "Subcommand for agent is required"))))
    }

    // Connect to control server
    info!("Connecting to control server '{}'", control_server);
    let (ws_stream, _) = match connect_async(control_server).await {
        Ok(it) => it,
        Err(err) => {
            let msg = format!("Failed connecting to the control server: {}", err);
            return Err(AgentError::StartupError(StartupError(BasicAgentError::new(&msg.to_string()))))
        }
    };
    let (ws_tx, ws_rx) = unbounded::<Message>();
    info!("Successful control server connection & message channel creation");

    // Agent-dependant logic
    if let Some(ref subparams) = params.subcommand_matches("adafruit-nrf52-sh") {
        // Parse agent parameters
        let baudrate: u32 = subparams.value_of_t("baudrate").unwrap_or_else(|e| e.exit());
        let device: PathBuf = subparams.value_of_t("device").unwrap_or_else(|e| e.exit());     
        if !device.exists() {
            return Err(AgentError::StartupError(StartupError(BasicAgentError::new(
                "Device file does not exist"))))
        }
        info!("Starting nRF52 agent");

        // Create monitoring sub-agent state
        debug!("Creating monitoring sub-agent state");
        #[derive(Debug)]
        struct AgentState {
            active_experiment: Uuid,
            active_monitor_handle: JoinHandle<()>,
            active_monitor_poison_pill: Arc<Mutex<bool>>, 
        };
        let agent_state: Arc<Mutex<Option<AgentState>>> = Arc::new(Mutex::from(None));

        // Connect agent to control server
        debug!("Attaching agent to control server");
        let (mut sink, stream) = ws_stream.split();
        let agent_to_ws = ws_rx.map(Ok).forward(&mut sink);

        // Parse message stream and react accordingly i.e. agent logic
        debug!("Awaiting messages from control server");
        let ws_to_stdout = stream.for_each(|message| async {
            // Unsafely fail if connection drops
            let data = message.unwrap().into_data();
            
            // Parse message as utf-8
            let utf8_data: &str = match str::from_utf8(&data) {
                Ok(it) => it,
                Err(err) => {
                    let info: String = format!("Invalid UTF-8 sequence: {}", err);
                    debug!("{}", info);
                    let message = OutgoingControlMessage::ParseErrorMessage(ParseErrorMessage { info });
                    if let Err(err) = send_outgoing_message(&ws_tx, &message) {
                        error!("Failed to send outgoing message about failure to parse UTF-8 message: {}", err);
                    };
                    return;
                },
            };
        
            // Parse utf-8 message as known incoming JSON message
            let incoming_message: IncomingMessage = match serde_json::from_str(utf8_data) {
                Ok(it) => it,
                Err(err) => {
                    let info = format!("Request contains unknown message: {}", err); 
                    debug!("{}", info);
                    let message = OutgoingControlMessage::ParseErrorMessage(ParseErrorMessage { info });
                    if let Err(err) = send_outgoing_message(&ws_tx, &message) {
                        error!("Failed to send outgoing message about failure to parse unknown message: {}", err);
                    };
                    return;
                }
            };

            // Perform agent logic based on incoming message
            match incoming_message {
                IncomingMessage::MonitorMessage(message) => {
                    // Check current monitor state
                    let mut agent_state_unlocked = match agent_state.try_lock() {
                        Ok(it) => it,
                        Err(err) => {
                            let info: String = format!("Failed to check nRF52 monitor state: {:?}", err);
                            debug!("{}", info);
                            let message = OutgoingControlMessage::MonitorErrorMessage(MonitorErrorMessage::ScriptRunError(ScriptRunError { info }));
                            if let Err(err) = send_outgoing_message(&ws_tx, &message) {
                                error!("Failed to send outgoing message about nRF52 monitor state error: {}", err);
                            };
                            return;
                        }
                    };

                    // If already monitoring, ignore control server request
                    if let Some(_) = *agent_state_unlocked {
                        debug!("Won't restart monitor, already monitoring");
                        let message = OutgoingControlMessage::MonitorErrorMessage(MonitorErrorMessage::AlreadyMonitoring(AlreadyMonitoring {}));
                        if let Err(err) = send_outgoing_message(&ws_tx, &message) {
                            error!("Failed to send outgoing message about nRF52 already monitoring: {}", err);
                        };
                        return;
                    }

                    // Not monitoring currently, so let's start a new monitor process
                    let mut monitor_command = match adafruit_nrf52_sh_agent::monitor_command(&device, baudrate) {
                        Ok(it) => it,
                        Err(err) => {
                            let info: String = format!("Failed to construct nRF52 monitor command: {:?}", err);
                            debug!("{}", info);
                            let message = OutgoingControlMessage::MonitorErrorMessage(MonitorErrorMessage::ScriptRunError(ScriptRunError { info }));
                            if let Err(err) = send_outgoing_message(&ws_tx, &message) {
                                error!("Failed to send outgoing message about nRF52 monitor construction error: {}", err);
                            };
                            return;
                        }
                    };
                    let active_monitor_handle: Child = match monitor_command.spawn() {
                        Ok(it) => it,
                        Err(err) => {
                            let info: String = format!("Failed to initialize nRF52 monitor command: {:?}", err);
                            debug!("{}", info);
                            let message = OutgoingControlMessage::MonitorErrorMessage(MonitorErrorMessage::ScriptRunError(ScriptRunError { info }));
                            if let Err(err) = send_outgoing_message(&ws_tx, &message) {
                                error!("Failed to send outgoing message about nRF52 monitor initialization error: {}", err);
                            };
                            return;
                        }
                    };
                    // let (mon_stdin, mon_stdout, mon_stderr) = match (active_monitor_handle.stdin, active_monitor_handle.stdout, active_monitor_handle.stderr) {
                    //     (Some(stdin), Some(stdout), Some(stderr)) => (stdin, stdout, stderr),
                    //     state => {
                    //         let info: String = format!("Failed to initialize communications with nRF52 monitor command");
                    //         debug!("{}: {:?}", info, state);
                    //         let message = OutgoingControlMessage::MonitorErrorMessage(MonitorErrorMessage::ScriptRunError(ScriptRunError { info }));
                    //         if let Err(err) = send_outgoing_message(&ws_tx, &message) {
                    //             error!("Failed to send outgoing message about nRF52 monitor communication initialization error: {}", err);
                    //         };
                    //         return;
                    //     }
                    // };

                    // Connect to monitor server
                    info!("Connecting to monitor server '{}'", *monitor_server);
                    let (mon_ws_stream, _) = match connect_async((*monitor_server).clone()).await {
                        Ok(it) => it,
                        Err(err) => {
                            let info: String = format!("Failed to connect to nRF52 monitor server: {:?}", err);
                            debug!("{}", info);
                            let message = OutgoingControlMessage::MonitorErrorMessage(MonitorErrorMessage::ConnectionError(ConnectionError { info }));
                            if let Err(err) = send_outgoing_message(&ws_tx, &message) {
                                error!("Failed to send outgoing message about nRF52 monitor server connection error: {}", err);
                            };
                            return;
                        }
                    };
                    let (mon_ws_tx, mon_ws_rx) = unbounded::<Message>();
                    info!("Successful monitor server connection & message channel creation");

                    let active_monitor_poison_pill = Arc::new(Mutex::new(false));
                    let parent_poison = Arc::clone(&active_monitor_poison_pill);
                    let child_poison = Arc::clone(&active_monitor_poison_pill);
                    let active_monitor = tokio::spawn(async move {
                        let fps = 1;
                        let delay = 1000 / fps;
                        let chunk_timestamp: u128 = create_timestamp();
                        let chunk = [0, 0];
                        // let mut stdout: Option<>
                        // loop {
                            // Check that we haven't been poisoned
                            // match child_poison.try_lock() {
                            //     Ok(it) => {
                            //         let is_poisoned: &bool = it.borrow();
                            //         if is_poisoned.clone() { break };
                            //     }
                            //     // poison state is unavailable, probably quite soon to being poisoned
                            //     _ => {}
                            // };

                            // Read and pipe forward stdout
                            let mut buf = [0, 10];
                            use tokio::io::AsyncReadExt;
                            use tokio::io::AsyncRead;
                            // use tokio::prelude::*;
                            sleep(Duration::from_millis(2000)).await;
                            match active_monitor_handle.stderr {
                                Some(mut out) => {
                                    let x = out.read(&mut buf[..]);
                                    let string = str::from_utf8(&buf);
                                    println!("{:?}", string);
                                },
                                None => {
                                    println!("No stdout");
                                }
                            }

                            // Let's wait a bit until the next io check
                            sleep(Duration::from_millis(delay)).await;
                        // }

                        // active_monitor_poison_pill
                        // mon_stdin, mon_stdout, mon_stderr
                        // mon_ws_tx, mon_ws_rx
                    });


                    *agent_state_unlocked = Some(AgentState {
                        active_experiment: message.experiment,
                        active_monitor_handle: active_monitor,
                        active_monitor_poison_pill: parent_poison
                    });

                    debug!("New monitor spawned: {:?}", *agent_state_unlocked);
                    // State lock guard goes out of scope and thereby will lock will become unlocked
                },
                IncomingMessage::UploadMessage(message) => {
                    // let binary_uuid = message.binary
                    // let upload_command = adafruit_nrf52_sh_agent::upload_command(&device, baudrate, message.binary);
                    println!("Upload: {}", message.binary);
                }
            }

            return;
        });

        pin_mut!(agent_to_ws, ws_to_stdout);
        future::select(agent_to_ws, ws_to_stdout).await;
    
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

fn send_outgoing_message(ws_tx: &UnboundedSender::<Message>, message: &OutgoingControlMessage) -> Result<(), BasicAgentError> {
    let serialized = match serde_json::to_string(&message) {
        Ok(it) => it,
        Err(err) => {
            let info = format!("Failed to serialize outgoing message: {}", err);
            return Err(BasicAgentError::new(&info))
        }
    };
    
    let response_message: Message = Message::Text(serialized);
    match ws_tx.unbounded_send(response_message) {
        Ok(it) => it,
        Err(err) => {
            let info = format!("Failed to send outgoing message: {}", err);
            return Err(BasicAgentError::new(&info))
        }
    };

    Ok(())
}

fn create_timestamp() -> u128 {
    SystemTime::now()
    .duration_since(UNIX_EPOCH)
    .expect("Current system time is before UNIX_EPOCH, fix clock")
    .as_millis()
}