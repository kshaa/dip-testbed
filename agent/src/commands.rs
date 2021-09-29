use serde::{Serialize, Deserialize};
use uuid::Uuid;

#[derive(Serialize, Deserialize, Debug)]
pub struct UploadMessage {
    binary: Uuid
}

#[derive(Serialize, Deserialize, Debug)]
pub struct MonitorMessage {
    experiment: Uuid
}

#[derive(Serialize, Deserialize, Debug)]
pub enum AgentMessage {
    UploadMessage,
    MonitorMessage,
}
