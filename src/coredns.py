"""Handle CoreDNS objects and print them accordingly"""

__all__ = [
    "CoreDNSObject",
    "CoreDNSPluginProperty",
    "CoreDNSPlugin",
    "CoreDNSZone",
    "CoreDNSCorefile",
    "PLUGIN_CACHE",
    "PLUGIN_LOG",
    "PLUGIN_ERRORS",
    "PLUGIN_FORWARD_CLOUDFLARE",
    "PLUGIN_FORWARD_GOOGLE",
    "PropertyDictType",
    "PluginDictType",
    "ZoneDictType"
]

from typing import (
    List,
    Optional,
    Dict,
    Generic,
    TypeVar,
    Union
)

_OT = TypeVar("_OT")
PropertyDictType = Dict[str, Union[str, List[str]]]
PluginDictType = Dict[str, Union[str, List[str], Dict[str, PropertyDictType]]]
ZoneDictType = Dict[str, Union[str, int, Dict[str, PluginDictType]]]


class CoreDNSObject(Generic[_OT]):
    """Base class for other CoreDNS classes"""

    def __init__(
            self,
            depth: int,
            name: str,
            *args: str,
            objects: Optional[Dict[str, _OT]] = None
    ):
        """Creates a base object

        Args:
            depth: This indicates how many tabs will be printed before object
            name: Name of the object
            *args: Arguments required by the object
            objects: A dictionary of objects that belongs current object
        Raises:
            ValueError: When depth is less than 0
        """

        if depth < 0:
            raise ValueError("Depth cannot be negative")

        if objects is None:
            objects = {}

        self.depth: int = depth
        self.name: str = name
        self.name_string: str = name
        self.args: List[str] = list(args)
        self.objects: Dict[str, _OT] = objects

    def to_caddy(self) -> str:
        """Return object and its objects in Caddy format"""

        result = '\t' * self.depth + self.name_string
        for arg in self.args:
            result += f" {arg}"

        if self.objects:
            result += " {\n"
            for obj in self.objects.values():
                result += f"{obj.to_caddy()}\n"
            result += '\t' * self.depth + "}"

        return result

    def __eq__(self, other: "CoreDNSObject"):
        if other is None:
            return False

        if self.depth != other.depth:
            return False

        if self.name != other.name:
            return False

        if len(self.args) != len(other.args):
            return False

        for i in range(len(self.args)):
            if self.args[i] != other.args[i]:
                return False

        if len(self.objects) != len(other.objects):
            return False

        for key in self.objects:
            if key not in other.objects:
                return False

            if self.objects[key] != other.objects[key]:
                return False

        return True

    def to_dict(self) -> Dict[str, Union[Dict[str, Dict], List[str], str, int]]:
        result = {
            "depth": self.depth,
            "name": self.name,
            "name_string": self.name_string,
            "args": self.args,
            "objects": {}
        }
        for key in self.objects:
            result["objects"][key] = self.objects[key].to_dict()

        return result

    def add_object(self, obj: _OT, replace: bool = True) -> Optional[_OT]:
        """Add an object of CoreDNSObject or one of it's subclasses

        Args:
            obj: Instance of the object to be added
            replace: Whether to replace existing object or not

        Returns:
            Returns newly added _OT object. If object already exists and
            replace is False, returns None
        """

        if obj.name in self.objects:
            if not replace:
                return None

        self.objects[obj.name] = obj
        return self.objects[obj.name]

    def remove_object(self, name: str) -> Optional[_OT]:
        """Remove an object

        Args:
            name: Name of the object to be removed

        Returns:
            Returns removed object if exists, returns None otherwise
        """

        return self.objects.pop(name, None)


class CoreDNSPluginProperty(CoreDNSObject):
    """Class for CoreDNS plugin properties"""

    def __init__(
            self,
            name: str,
            *args: str
    ):
        """

        Args:
            name: Name of the property
            *args: Arguments required by the property
        """

        super(CoreDNSPluginProperty, self).__init__(2, name, *args)

    @staticmethod
    def from_dict(d: PropertyDictType) -> "CoreDNSPluginProperty":
        return CoreDNSPluginProperty(
            d["name"],
            *d["args"]
        )


class CoreDNSPlugin(CoreDNSObject[CoreDNSPluginProperty]):
    """Class for CoreDNS plugins"""

    def __init__(
            self,
            name: str,
            *args: str,
            properties: Optional[Dict[str, CoreDNSPluginProperty]] = None
    ):
        """Creates a plugin object

        Args:
            name: Name of the plugin
            *args: Arguments required by plugin
            properties: Properties required by plugin
        """

        super(CoreDNSPlugin, self).__init__(1, name, *args, objects=properties)

    @staticmethod
    def from_dict(d: PluginDictType) -> "CoreDNSObject":
        return CoreDNSPlugin(
            d["name"],
            *d["args"],
            properties={
                key: CoreDNSPluginProperty.from_dict(d["objects"][key]) for key in d["objects"]
            }
        )

    def add_property(
            self,
            name: str,
            *args: str,
            replace: bool = True
    ) -> Optional[CoreDNSPluginProperty]:
        """Add new property

        Args:
            name: Name of the property
            *args: Arguments required by the property
            replace: Whether to replace existing property or not

        Returns:
            Returns newly added CoreDNSPluginProperty object. If property
            already exists and replace is False, returns None
        """

        return self.add_object(CoreDNSPluginProperty(name, *args), replace=replace)


class CoreDNSZone(CoreDNSObject[CoreDNSPlugin]):
    """Class for CoreDNS zones"""

    def __init__(
            self,
            name: str,
            port: int = 53,
            plugins: Optional[Dict[str, CoreDNSPlugin]] = None
    ):
        """Creates a zone object

        Args:
            name: Name of the zone
            port: Port
            plugins: Plugins required by the zone
        Raises:
            ValueError: When port is negative
        """

        super(CoreDNSZone, self).__init__(0, name, objects=plugins)

        if port < 0:
            raise ValueError("Port cannot be negative")

        self.port = port
        self.name_string = "{}:{}".format(self.name, self.port)

    def __eq__(self, other: "CoreDNSZone"):
        if not super(CoreDNSZone, self).__eq__(other):
            return False

        return self.port == other.port

    def to_dict(self) -> Dict[str, Union[Dict[str, Dict], List[str], str, int]]:
        result = super(CoreDNSZone, self).to_dict()
        result["port"] = self.port
        return result

    @staticmethod
    def from_dict(d: ZoneDictType) -> "CoreDNSZone":
        return CoreDNSZone(
            d["name"],
            port=d["port"],
            plugins={
                key: CoreDNSPlugin.from_dict(d["objects"][key]) for key in d["objects"]
            }
        )

    def add_plugin(
            self,
            name: str,
            *args: str,
            properties: Optional[Dict[str, CoreDNSPluginProperty]] = None,
            replace: bool = None
    ) -> Optional[CoreDNSPlugin]:
        """Add new plugin

        Args:
            name: Name of the plugin
            *args: Args required by the plugin
            properties: Properties of the plugin
            replace: Whether to replace existing plugin or not

        Returns:
            Returns newly added CoreDNSPlugin object. If plugin already
            exists and replace is False, returns None
        """

        new_plugin = CoreDNSPlugin(name, *args, properties=properties)
        return self.add_object(new_plugin, replace=replace)


class CoreDNSCorefile(CoreDNSObject[CoreDNSZone]):
    """Class representing CoreDNS 'Corefile'"""

    def __init__(
            self,
            zones: Dict[str, "CoreDNSZone"]
    ):
        """Creates a corefile object

        Args:
            zones: Zones that will be included in the Corefile
        """
        super(CoreDNSCorefile, self).__init__(0, "", objects=zones)

        if len(self.objects) == 0:
            raise ValueError("At least one zone required")

    def to_caddy(self) -> str:
        result = ""
        for zone in self.objects.values():
            result += f"{zone.to_caddy()}\n\n"
        return result.strip()

    def to_dict(self) -> Dict[str, Dict]:
        return {key: self.objects[key].to_dict() for key in self.objects}

    @staticmethod
    def from_dict(d) -> "CoreDNSCorefile":
        return CoreDNSCorefile(
            zones={key: CoreDNSZone.from_dict(d[key]) for key in d}
        )

    def add_zone(
            self,
            name: str,
            port: int = 53,
            plugins: Optional[Dict[str, CoreDNSPlugin]] = None,
            replace: bool = True
    ) -> Optional[CoreDNSZone]:
        """Add new zone

        Args:
            name: Name of the zone
            port: Port that zone uses
            plugins: Plugins required by the zone
            replace: Whether to replace existing zone or not

        Returns:
            Returns newly added CoreDNSZone object. If already exists
            and replace is False, returns None
        """

        new_zone = CoreDNSZone(name, port, plugins)
        return self.add_object(new_zone, replace=replace)


# Some plugin definitions for the sake of simplicity
PLUGIN_CACHE = CoreDNSPlugin("cache")
PLUGIN_LOG = CoreDNSPlugin("log")
PLUGIN_ERRORS = CoreDNSPlugin("errors")
PLUGIN_FORWARD_GOOGLE = CoreDNSPlugin("forward", ".", "8.8.8.8", "8.8.4.4")
PLUGIN_FORWARD_CLOUDFLARE = CoreDNSPlugin("forward", ".", "1.1.1.1", "1.0.0.1")
