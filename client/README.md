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
