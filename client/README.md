# DIP Testbed Client
  
## Usage
### Development
- Install `pipenv` for dependency management  
- Run `pipenv install --dev` for development dependency download  
- Run `pipenv shell` to enter project-specific python environment  
- Run `./typecheck.sh` to test static type checks  
- Run `./test.sh` to run unit tests  
- Run `./lint.sh` to run linter
- Run `./check.sh` to run all aforementioned types of tests
- Run `./dip_client.py --help` to print client CLI usage definition
- Run `./build.sh` to create a single executable client file

### Built client
- Run `./dist/dip_client --help` to print built client CLI usage definition

### File tree
- `main.py` is just an entrypoint for the CLI interface from `service/click.py`
- `service/click.py` and `service/cli.py` define a CLI interface for all possible DIP client commands:
    - Generic one-off client commands are defined mostly in `service/backend.py`
    - Persistent event engine agent commands are defined in `agent/*`, `monitor/*`, `engine/*`
- `agent_entrypoints.py` prepare and run a configured agent `agent.py`
- `agent/agent.py` runs using an `AgentConfig` i.e. an `Engine` attached to `SocketInterface` with the help of message `Codec`s
- `engine/engine.py` defines a base `Engine` which starts, stops, receives messages, processes events, executes side-effects
- `engine/board/*` define engines to handle hardware board lifecycle - heartbeats, firmware uploads, monitoring
- `engine/video/*` define video streaming engines using VLC
- `monitor/*` define serial monitoring interfaces
- Agents use `ws.py` to exchange WebSocket messages
- Agents more specifically SocketInterfaces use `protocol/*` to encode/decode messages
