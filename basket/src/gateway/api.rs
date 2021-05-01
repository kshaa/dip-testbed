use std::option::Option;

pub trait Gateway {
    fn send(&self, data: &[u8]) -> Option<String>;
}
