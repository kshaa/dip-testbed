use tempfile::NamedTempFile;
use std::io::Write;
use std::path::PathBuf;
use tokio::process::Command;
use crate::errors;
use errors::*;

pub static MONITOR_SCRIPT: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/src/adafruit_nrf52_sh_agent/monitor.sh"));
pub static UPLOAD_SCRIPT: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/src/adafruit_nrf52_sh_agent/upload.sh"));

pub fn monitor(
    device: PathBuf,
    baudrate: u32,
    firmware: PathBuf
) -> Result<Command, MonitorError> {
    let mut monitor_script_file: NamedTempFile = match NamedTempFile::new() {
        Ok(it) => it,
        Err(err) => {
            let msg = format!("Failed to create temporary for nRF52 agent's monitor script file: {}", err);
            return Err(MonitorError::TempFileError(TempFileError(BasicAgentError::new(&msg.to_string()))))}
    };

    match monitor_script_file.write_all(MONITOR_SCRIPT.as_bytes()) {
        Ok(it) => it,
        Err(err) => {
            let msg = format!("Failed to write temporary for nRF52 agent's monitor script file: {}", err);
            return Err(MonitorError::TempFileError(TempFileError(BasicAgentError::new(&msg.to_string()))))
        }
    };

    let monitor_script_path: &str = match monitor_script_file.path().to_str() {
        Some(it) => it,
        None => return Err(MonitorError::TempFileError(TempFileError(BasicAgentError::new(
            "Failed to process path for nRF52 agent's monitor script file"))))
    };

    let device_path: &str = match device.to_str() {
        Some(it) => it,
        None => return Err(MonitorError::TempFileError(TempFileError(BasicAgentError::new(
            "Failed to process path for nRF52 device file"))))
    };

    let firmware_path: &str = match firmware.to_str() {
        Some(it) => it,
        None => return Err(MonitorError::TempFileError(TempFileError(BasicAgentError::new(
            "Failed to process path for nRF52 device file"))))
    };

    let mut monitor_command = Command::new("bash");
    monitor_command
        .arg(monitor_script_path)
        .arg("-d".to_string()).arg(device_path)
        .arg("-b".to_string()).arg(baudrate.to_string())
        .arg("-f".to_string()).arg(firmware_path);

    Ok(monitor_command)
}
