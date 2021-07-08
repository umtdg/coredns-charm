# coredns-k8s

## Description

CoreDNS server using Kubernetes clusters with sidecar pattern via Pebble.

## Usage

There are two options for Corefile configuration:
* Use a script file (i.e. [coredns_script.txt](coredns_script.txt)),
* Use Juju actions

A default Corefile will always be generated and each option applies to that particular
default Corefile.

### Script file

A script file used for Corefile generation. Each line **not** starting with `#` is
considered as command and executed accordingly. CoreDNS service will be started after
the execution of `script-file`.

Syntax of the commands are the same with actions except names uses underscore as 
a replacement of dash. For example, if an action's name is `add-property`, then it 
is used as `add_property` in `script-file`.

Changes made by each command will be applied to a default Corefile. To generate
a Corefile from scratch, use `reset` in `script-file`.

There is no `update` command in `script-file` since generation of Corefile will be
after the execution of `script-file`.

## Config

There are currently no configs

## Deployment

In order to deploy, there are two resources:
* An OCI image containing CoreDNS executable in '/' (TODO: Add config for CoreDNS
  executable path and Corefile path)
* A custom script file containing commands in each line

## Actions

To see the actions defined:

    # juju actions coredns-k8s

To show detailed information for an action:

    # juju show-action coredns-k8s/<unit_number> <action_name>

Alternatively, you can view [actions.yaml](actions.yaml).

## Developing

Create and activate a virtualenv with the development requirements:

    $ virtualenv -p python3 venv
    $ source venv/bin/activate
    $ pip install -r requirements-dev.txt

## Testing

The Python operator framework includes a very nice harness for testing
operator behaviour without full deployment. Just `run_tests`:

    $ ./run_tests

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
