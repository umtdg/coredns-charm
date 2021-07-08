# coredns-k8s

## Description

CoreDNS server using Kubernetes clusters with sidecar pattern via Pebble

## Usage

### Config

There are currently no configs

### Deployment

In order to deploy, there are two resources:
* An OCI image containing CoreDNS executable in '/' (There will be a config for this)
* A custom script file containing commands in each line

#### Script file

The commands in the file are parsed line by line by charm itself and CoreDNS config is updated accordingly. Syntax of these commands is similar to actions.

For a list of commands see: [Commands](command_list.md)

### Actions

Actions have the same syntax with commands in [command_list.md](command_list.md)

## Developing

Create and activate a virtualenv with the development requirements:

    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -r requirements-dev.txt

## Testing

The Python operator framework includes a very nice harness for testing
operator behaviour without full deployment. Just `run_tests`:

    ./run_tests

## TODO
- [x] ~~Add action/actions to view a single zone, Corefile, or a zone file~~
- [x] ~~Add/remove properties to/from CoreDNS plugins in Corefile using actions~~
- [x] ~~Add/remove CoreDNS plugins to/from Corefile~~
- [x] ~~Add/remove zones to/from Corefile~~
- [x] ~~Proper resulting for actions~~
- [x] ~~Add option to keep zone file when removing a zone with file plugin~~
- [x] ~~Add parser to read and execute commands from file~~
- [x] ~~Change `__str__` to a different method~~
- [ ] Better default Corefile with configs
- [ ] Add/remove records to/from zone files
- [ ] Unit tests for print actions
- [ ] Unit tests for add/remove property actions
- [ ] Unit tests for add/remove plugin actions
- [ ] Unit tests for add/remove zone actions
- [ ] Unit tests for add/remove record actions
- [ ] Support for adding 'file' plugin (Create corresponding file)
- [ ] Support for removing 'file' plugin (Remove corresponding file)
- [ ] Add replace option for 'add' actions
- [ ] Add config to specify a directory to store CoreDNS files (Corefile and DNS zone files)
