use serde::{Serialize, Deserialize};
use uuid::Uuid;

#[derive(Serialize, Deserialize, Debug)]
pub struct UploadMessage {
    pub binary: Uuid
}

#[derive(Serialize, Deserialize, Debug)]
pub struct MonitorMessage {
    pub experiment: Uuid
}

#[derive(Serialize, Deserialize, Debug)]
pub struct ParseMessage {
    pub info: String
}

#[derive(Serialize, Deserialize, Debug)]
pub enum IncomingMessage {
    UploadMessage(UploadMessage),
    MonitorMessage(MonitorMessage),
}

#[derive(Serialize, Deserialize, Debug)]
pub enum OutgoingMessage {
    ParseMessage(ParseMessage),
}

#[test]
fn serde_format_reality_check() {
    let experiment: Uuid = Uuid::parse_str("14bc4472-21f5-11ec-a6ef-13ef7ae4bd77").unwrap();
    let message: IncomingMessage = IncomingMessage::MonitorMessage(MonitorMessage {
        experiment
    });
    let serialized = serde_json::to_string(&message).unwrap();
    let expected = "{\"MonitorMessage\":{\"experiment\":\"14bc4472-21f5-11ec-a6ef-13ef7ae4bd77\"}}";
    assert_eq!(serialized, expected);

    let unserialized: IncomingMessage = serde_json::from_str(&serialized).unwrap();
    let unserialized_experiment = match unserialized {
        IncomingMessage::MonitorMessage(it) => it.experiment,
        _ => panic!("MonitorMessage couldn't be unserialized")
    };

    assert_eq!(unserialized_experiment, experiment);
}
