# DIP Testbed Client
  
## Usage
- Install `pipenv` for dependency management  
- Run `pipenv install --dev` for development dependency download  
- Run `pipenv shell` to enter project-specific python environment  
- Run `./typecheck.sh` to test static type checks  
- Run `./test.sh` to run unit tests  
- Run `./lint.sh` to run linter
- Run `./check.sh` to run all aforementioned types of tests
- Define `LOG_LEVEL` environment variable to configure logging verbosity  
- Run `./dip_client.py --help` to print client CLI usage definition
- Run `pyinstaller dip_client.spec` to create a single executable client file  
