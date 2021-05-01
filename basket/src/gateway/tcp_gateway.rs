use std::option::Option;
use std::cell::{RefCell, RefMut};
use std::net::TcpStream;
use std::io::Write;
use super::api::Gateway;

pub struct TCPGateway {
    maybe_stream_ref_cell: RefCell<Result<TcpStream, String>>,
    pub host: String,
    pub port: u16
}

impl TCPGateway {
    pub fn init(_host: String, _port: u16) -> TCPGateway {
        let gateway = TCPGateway {
            maybe_stream_ref_cell: RefCell::new(Err("Gateway not initialized".to_owned())),
            host: _host,
            port: _port
        };
        gateway.reconnect_gateway();
        gateway
    }

    fn reconnect_gateway(&self) -> Option<String> {
        // Check connection status (or fail)
        let mut is_connected: bool = false;
        match self.maybe_stream_ref_cell.try_borrow_mut() {
            Err(e) => return Some(format!("Failed to borrow TCP stream for reconnection: {}", e)),
            Ok(maybe_stream_ref) => RefMut::map(maybe_stream_ref, |maybe_stream| {
                is_connected = maybe_stream.is_ok();
                maybe_stream
            }),
        };

        // Attempt to reconnect
        if !is_connected {
            let mut connect_error = None;
            let _ = self.maybe_stream_ref_cell.replace_with(|_| {
                TcpStream::connect((self.host.clone(), self.port))
                    .map_err(|err| err.to_string())
                    .map_err(|err| {
                        connect_error = Some(format!("Failed to reconnect TCP stream: {}", err));
                        err
                    })
            });
            connect_error
        } else {
            None
        }
    }
}

impl Gateway for TCPGateway {
    fn send(&self, data: &[u8]) -> Option<String> {
        // Attempt to reconnect
        self.reconnect_gateway().map(|err| {
            return Some(format!("Failed to reconnect: {}", err));
        });

        // Attempt to borrow connection ownership
        let maybe_stream_ref = match self.maybe_stream_ref_cell.try_borrow_mut() {
            Err(err) => return Some(format!("Failed to borrow TCP stream for send: {}", err)),
            Ok(maybe_stream_ref) => maybe_stream_ref
        };

        // Attempt to check connection status & send message
        let mut result: Option<String> = None;
        RefMut::map(maybe_stream_ref, |maybe_stream| {
            result = match maybe_stream {
                Err(err) => Some(format!("TCP connection is not available: {}", err)),
                Ok(stream) => {
                    let write = match stream.write(data) {
                        Err(err) => Some(format!("Failed to write bytes to TCP stream: {}", err)),
                        Ok(_) => None,
                    };
            
                    match write {
                        Some(err) => Some(err),
                        None => match stream.flush() {
                            Err(err) => Some(format!("Failed to flush bytes to TCP stream: {}", err)),
                            Ok(_) => None,
                        }
                    }
                },
            };
            maybe_stream
        });
        result
    }
}
