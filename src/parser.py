import shlex
import enum

from typing import (
    Dict,
    Callable,
    Optional,
    List,
)

from coredns import (
    CoreDNSCorefile,
    CoreDNSObject
)


class ResultType(enum.Enum):
    ADD_NO_REPLACE = "Not replacing, nothing changed"
    REMOVE_NOT_FOUND = "Not found, nothing changed"


class ValidationError(Exception):
    def __init__(self, message: str = ""):
        super(ValidationError, self).__init__(message)
        self.message = message


class RequiredError(Exception):
    def __init__(self, message: str = ""):
        super(RequiredError, self).__init__(message)
        self.message = message


class Parser:
    @staticmethod
    def return_result_if_none(obj: Optional[CoreDNSObject], result_type: ResultType) -> str:
        if obj is None:
            return result_type.value
        else:
            return obj.to_caddy()

    @staticmethod
    def raise_required(given, required):
        missing = []
        for arg in required:
            if arg not in given:
                missing.append(arg)

        if missing:
            raise RequiredError(f"Missing required arguments: {missing}")

    @staticmethod
    def validate_plugin_owners(corefile: CoreDNSCorefile, zone: str):
        if zone not in corefile.objects:
            raise ValidationError(f"Could not found given zone {zone}")

    @staticmethod
    def validate_property_owners(corefile: CoreDNSCorefile, plugin: str, zone: str):
        try:
            Parser.validate_plugin_owners(corefile, zone)
        except ValidationError as e:
            raise e

        if plugin not in corefile.objects[zone].objects:
            raise ValidationError(f"Could not found given plugin {plugin}")

    @staticmethod
    def str2bool(s: str) -> bool:
        return s.lower() in ["true", "yes"]

    @staticmethod
    def convert_params(
            params: Dict,
            conversion_map: Optional[Dict] = None
    ):
        if conversion_map is None:
            conversion_map = {
                "args": str.split,
                "port": int,
                "replace": Parser.str2bool
            }

        for arg in conversion_map:
            if arg in params:
                params[arg] = conversion_map[arg](params[arg])

    @staticmethod
    def default_params(
            params: Dict,
            defaults: Dict,
            convert: bool = True,
            conversion_map: Optional[Dict] = None
    ):
        for default in defaults:
            if default not in params:
                params[default] = defaults[default]

        if convert:
            Parser.convert_params(params, conversion_map)

    @staticmethod
    def parse_args(cmd: str) -> Dict:
        lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lexer.wordchars += '='

        params = dict(word.split('=', maxsplit=1) for word in lexer)

        Parser.default_params(
            params,
            {
                "args": "",
                "replace": "true"
            },
            convert=True
        )

        return params

    @staticmethod
    def reset(corefile: CoreDNSCorefile, _=None) -> str:
        corefile.objects = {}
        return ""

    @staticmethod
    def add_property(corefile: CoreDNSCorefile, params: Dict) -> str:
        Parser.raise_required(params, ["name", "plugin", "zone"])

        name: str = params["name"]
        zone: str = params["zone"]
        plugin: str = params["plugin"]
        args: List[str] = params["args"]
        replace: bool = params["replace"]

        Parser.validate_property_owners(corefile, plugin, zone)

        added = corefile.objects[zone].objects[plugin].add_property(
            name,
            *args,
            replace=replace
        )
        return Parser.return_result_if_none(added, ResultType.ADD_NO_REPLACE)

    @staticmethod
    def remove_property(corefile: CoreDNSCorefile, params: Dict) -> str:
        Parser.raise_required(params, ["name", "plugin", "zone"])

        name: str = params["name"]
        zone: str = params["zone"]
        plugin: str = params["plugin"]

        Parser.validate_property_owners(corefile, plugin, zone)

        removed = corefile.objects[zone].objects[plugin].remove_object(name)
        return Parser.return_result_if_none(removed, ResultType.REMOVE_NOT_FOUND)

    @staticmethod
    def add_plugin(corefile: CoreDNSCorefile, params: Dict) -> str:
        Parser.raise_required(params, ["name", "zone"])

        name: str = params["name"]
        zone: str = params["zone"]
        args: List[str] = params["args"]
        replace: bool = params["replace"]

        Parser.validate_plugin_owners(corefile, zone)

        added = corefile.objects[zone].add_plugin(
            name,
            *args,
            replace=replace
        )
        return Parser.return_result_if_none(added, ResultType.ADD_NO_REPLACE)

    @staticmethod
    def remove_plugin(corefile: CoreDNSCorefile, params: Dict) -> str:
        Parser.raise_required(params, ["name", "zone"])

        name: str = params["name"]
        zone: str = params["zone"]

        Parser.validate_plugin_owners(corefile, zone)

        removed = corefile.objects[zone].remove_object(name)
        return Parser.return_result_if_none(removed, ResultType.REMOVE_NOT_FOUND)

    @staticmethod
    def add_zone(corefile: CoreDNSCorefile, params: Dict) -> str:
        Parser.raise_required(params, ["name"])

        Parser.default_params(
            params,
            {"port": "53"},
            convert=True,
            conversion_map={"port": int}
        )

        name: str = params["name"]
        port: int = params["port"]
        replace: bool = params["replace"]

        added = corefile.add_zone(name, port, replace=replace)

        return Parser.return_result_if_none(added, ResultType.ADD_NO_REPLACE)

    @staticmethod
    def remove_zone(corefile: CoreDNSCorefile, params: Dict) -> str:
        Parser.raise_required(params, ["name"])

        zone = corefile.remove_object(params["name"])
        return Parser.return_result_if_none(zone, ResultType.REMOVE_NOT_FOUND)

    @staticmethod
    def exec(corefile: CoreDNSCorefile, filename: str):
        with open(filename, "r") as f:
            line_number = 0
            for line in f.readlines():
                line_number += 1
                if line.startswith('#') or not line or line.isspace():
                    continue

                cmd = line.split(maxsplit=1)
                if cmd[0] in PARSER_COMMANDS:
                    params = Parser.parse_args(cmd[1])
                    PARSER_COMMANDS[cmd[0]](corefile, params)
                else:
                    raise RuntimeError(f"Unknown command '{cmd[0]}' in line {line_number}")


PARSER_COMMANDS: Dict[str, Callable[[CoreDNSCorefile, Dict], str]] = {
    "reset": Parser.reset,
    "add_property": Parser.add_property,
    "remove_property": Parser.remove_property,
    "add_plugin": Parser.add_plugin,
    "remove_plugin": Parser.remove_plugin,
    "add_zone": Parser.add_zone,
    "remove_zone": Parser.remove_zone
}
