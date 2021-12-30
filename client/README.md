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
- `dip_client.py` is just an entrypoint for the CLI interface from `cli.py`
- `cli.py` defines a CLI interface for all possible DIP client commands:
    - Generic one-off client commands are defined in `backend_util.py`
    - Microcontroller agent commands are defined in `agent_entrypoints.py`
- `agent_entrypoints.py` prepare and run a configured agent `agent.py`
- `agent.py` runs using an `AgentConfig`, `Engine`, serialization `Encoder`/`Decoder`
- `agent_util.py` defines a base `AgentConfig`
- `engine.py` defines a base `Engine`
- `agent_*.py` define custom `Engine`s and `AgentConfig`s
- Agents use `ws.py` to exchange WebSocket messages
- Agents use `s11n_*.py` to serialize messages
- Agents use `Engine` for stateful actions & resulting messages
