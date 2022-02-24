# DIP Testbed
  
DIP Testbed Platform is an academic work which allows users to remotely program and experience physical, embedded devices through various virtual interfaces (uni-directional webcam stream, bi-directional serial connection stream).  
  
## Installation
### Quick install
```bash
curl https://github.com/kshaa/dip-testbed-dist/releases/latest/download/client_install.sh | bash
```
  
_Note: This assumes usage of bash, AMD64 architecture, testbed.veinbahs.lv as default server_  

### Manual install
- Download `https://github.com/kshaa/dip-testbed-dist/releases/latest/download/dip_client_${TARGET_ARCH}`  
- Store in `${PATH}`
- Set executable bit
- Set static URL using `dip_client session-static-server -s http://testbed.veinbahs.lv`
- Set control URL using `dip_client session-control-server -s ws://testbed.veinbahs.lv`
  
## Usage
```bash
dip_client session-auth -u <username> -p <password>
```
  
## Documentation
- See 🌼 🌻 [docs](./docs/README.md) 🌻 🌼 for user-centric documentation  
- See [prototypes](./prototypes/README.md) for examples of the testbed platform usage  
  
## Development
The following links are currently available only by special request  
  
- See [backend](./backend/README.md) for backend usage  
- See [client](./client/README.md) for client and agent usage
- See [database](./database/README.md) for database usage  
  