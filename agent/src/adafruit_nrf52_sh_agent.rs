use tempfile::NamedTempFile;
use std::io::Write;
use std::path::PathBuf;
use tokio::process::Command;
use crate::errors;
use errors::*;

pub static MONITOR_SCRIPT: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/src/adafruit_nrf52_sh_agent/monitor.sh"));
pub static UPLOAD_SCRIPT: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/src/adafruit_nrf52_sh_agent/upload.sh"));

pub fn monitor_command(
    device: &PathBuf,
    baudrate: u32
) -> Result<Command, MonitorError> {
    let mut monitor_script_file: NamedTempFile = match NamedTempFile::new() {
        Ok(it) => it,
        Err(err) => {
            let msg = format!("Failed to create temporary for nRF52 agent's monitor script file: {}", err);
            return Err(MonitorError::TempFileError(TempFileError(BasicAgentError::new(&msg.to_string()))))}
    };

    if let Err(err) = monitor_script_file.write_all(MONITOR_SCRIPT.as_bytes()) {
        let msg = format!("Failed to write temporary for nRF52 agent's monitor script file: {}", err);
        return Err(MonitorError::TempFileError(TempFileError(BasicAgentError::new(&msg.to_string()))))
    }

    // let monitor_script_path: &str = match monitor_script_file.path().clone().to_str() {
    //     Some(it) => it,
    //     None => return Err(MonitorError::TempFileError(TempFileError(BasicAgentError::new(
    //         "Failed to process path for nRF52 agent's monitor script file"))))
    // };

    let monitor_script_pathbuf = match monitor_script_file.keep() {
        Ok((_, pathbuf)) => pathbuf,
        Err(err) => {
            let msg = format!("Failed to persist temporary for nRF52 agent's monitor script file: {}", err);
            return Err(MonitorError::TempFileError(TempFileError(BasicAgentError::new(&msg.to_string()))))
        }
    };

    let monitor_script_path = match monitor_script_pathbuf.to_str() {
        Some(it) => it,
        None =>
            return Err(MonitorError::TempFileError(TempFileError(BasicAgentError::new(
                "Failed to process path for nRF52 agent's monitor script file"))))
    };

    let device_path: &str = match device.to_str() {
        Some(it) => it,
        None => return Err(MonitorError::TempFileError(TempFileError(BasicAgentError::new(
            "Failed to process path for nRF52 device file"))))
    };

    let mut monitor_command = Command::new("bash");
    monitor_command
        .arg(monitor_script_path)
        .arg("-d".to_string()).arg(device_path)
        .arg("-b".to_string()).arg(baudrate.to_string());

    Ok(monitor_command)
}

pub fn upload_command(
    device: &PathBuf,
    baudrate: u32,
    firmware: &PathBuf
) -> Result<Command, UploadError> {
    let mut upload_script_file: NamedTempFile = match NamedTempFile::new() {
        Ok(it) => it,
        Err(err) => {
            let msg = format!("Failed to create temporary for nRF52 agent's upload script file: {}", err);
            return Err(UploadError::TempFileError(TempFileError(BasicAgentError::new(&msg.to_string()))))}
    };

    match upload_script_file.write_all(MONITOR_SCRIPT.as_bytes()) {
        Ok(it) => it,
        Err(err) => {
            let msg = format!("Failed to write temporary for nRF52 agent's upload script file: {}", err);
            return Err(UploadError::TempFileError(TempFileError(BasicAgentError::new(&msg.to_string()))))
        }
    };

    let upload_script_path: &str = match upload_script_file.path().to_str() {
        Some(it) => it,
        None => return Err(UploadError::TempFileError(TempFileError(BasicAgentError::new(
            "Failed to process path for nRF52 agent's upload script file"))))
    };

    let device_path: &str = match device.to_str() {
        Some(it) => it,
        None => return Err(UploadError::TempFileError(TempFileError(BasicAgentError::new(
            "Failed to process path for nRF52 device file"))))
    };

    let firmware_path: &str = match firmware.to_str() {
        Some(it) => it,
        None => return Err(UploadError::TempFileError(TempFileError(BasicAgentError::new(
            "Failed to process path for nRF52 firmware file"))))
    };

    let mut upload_command = Command::new("bash");
    upload_command
        .arg(upload_script_path)
        .arg("-d".to_string()).arg(device_path)
        .arg("-b".to_string()).arg(baudrate.to_string())
        .arg("-f".to_string()).arg(firmware_path);

    Ok(upload_command)
}
