use std::fmt::{Display, Formatter, Result as FmtResult};
use std::error;

// Basic AgentError implementation
#[derive(Debug)]
pub struct BasicAgentError {
    details: String
}

impl BasicAgentError {
    pub fn new(msg: &str) -> BasicAgentError {
        BasicAgentError { details: msg.to_string() }
    }
}

impl Display for BasicAgentError {
    fn fmt(&self, f: &mut Formatter) -> FmtResult {
        write!(f, "{}", self.details)
    }
}

impl error::Error for BasicAgentError {
    fn description(&self) -> &str {
        &self.details
    }
}

#[derive(Debug)]
pub struct StartupError(pub BasicAgentError);

#[derive(Debug)]
pub struct TempFileError(pub BasicAgentError);

#[derive(Debug)]
pub enum MonitorError {
    TempFileError(TempFileError)
}

#[derive(Debug)]
pub enum AgentError {
    StartupError(StartupError),
    MonitorError(MonitorError),
}