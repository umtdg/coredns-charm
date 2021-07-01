import unittest

from coredns import (
    CoreDNSObject,
    CoreDNSPluginProperty,
    CoreDNSPlugin,
    CoreDNSZone,
    CoreDNSCorefile
)


class TestCoreDNS(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None

    # CoreDNSObject tests
    def test_base_object_init_no_raise(self):
        try:
            obj1 = CoreDNSObject(0, "obj1", "arg1", "arg2")
            obj2 = CoreDNSObject(1, "obj2")
        except ValueError:
            self.fail("CoreDNSObject.__init__ raised ValueError")

        self.assertEqual(obj1.depth, 0)
        self.assertEqual(obj1.name, "obj1")
        self.assertListEqual(obj1.args, ["arg1", "arg2"])

        self.assertEqual(obj2.depth, 1)
        self.assertEqual(obj2.name, "obj2")
        self.assertListEqual(obj2.args, [])

    def test_base_object_init_raise(self):
        self.assertRaises(ValueError, CoreDNSObject, -1, "name", "arg1", "arg2")

    def test_base_object_to_caddy(self):
        obj1 = CoreDNSObject(0, "obj1", "arg1", "arg2")
        obj2 = CoreDNSObject(1, "obj2")

        self.assertEqual(obj1.to_caddy(), "obj1 arg1 arg2")
        self.assertEqual(obj2.to_caddy(), "\tobj2")

    def test_base_object_eq(self):
        obj1 = CoreDNSObject(0, "obj1", "arg1", "arg2")
        obj2 = CoreDNSObject(0, "obj1", "arg1", "arg2")
        obj3 = CoreDNSObject(1, "obj1", "arg1", "arg2")
        obj4 = CoreDNSObject(0, "obj2", "arg1", "arg2")
        obj5 = CoreDNSObject(0, "obj1", "arg1", "arg3")
        obj6 = CoreDNSObject(0, "obj1", "arg1")
        obj7 = None

        self.assertTrue(obj1 == obj2)
        self.assertFalse(obj1 == obj3)
        self.assertFalse(obj1 == obj4)
        self.assertFalse(obj1 == obj5)
        self.assertFalse(obj1 == obj6)
        self.assertFalse(obj1 == obj7)

    # CoreDNSPluginProperty tests
    def test_property_to_dict(self):
        prop1 = CoreDNSPluginProperty("prop1", "arg1", "arg2")
        prop2 = CoreDNSPluginProperty("prop2")

        self.assertDictEqual(prop1.to_dict(), {
            "depth": 2,
            "name": "prop1",
            "name_string": "prop1",
            "args": ["arg1", "arg2"],
            "objects": {}
        })
        self.assertDictEqual(prop2.to_dict(), {
            "depth": 2,
            "name": "prop2",
            "name_string": "prop2",
            "args": [],
            "objects": {}
        })

    def test_property_from_dict(self):
        prop = CoreDNSPluginProperty.from_dict({
            "name": "prop1",
            "args": ["arg1", "arg2"]
        })

        self.assertEqual(prop, CoreDNSPluginProperty("prop1", "arg1", "arg2"))

    # CoreDNSPlugin tests
    def test_plugin_init(self):
        plugin1 = CoreDNSPlugin(
            "plugin1",
            "arg1",
            "arg2",
            properties={
                "prop1": CoreDNSPluginProperty("prop1", "arg1"),
                "prop2": CoreDNSPluginProperty("prop2")
            }
        )
        plugin2 = CoreDNSPlugin("plugin2", "arg1")

        self.assertDictEqual(
            plugin1.objects,
            {
                "prop1": CoreDNSPluginProperty("prop1", "arg1"),
                "prop2": CoreDNSPluginProperty("prop2")
            }
        )
        self.assertDictEqual(plugin2.objects, {})

    def test_plugin_to_caddy(self):
        plugin1 = CoreDNSPlugin("plugin1", "arg1", "arg2")
        plugin2 = CoreDNSPlugin("plugin2", "arg1", "arg2", properties={
            "prop1": CoreDNSPluginProperty("prop1", "arg1"),
            "prop2": CoreDNSPluginProperty("prop2")
        })

        self.assertEqual(plugin1.to_caddy(), "\tplugin1 arg1 arg2")
        self.assertEqual(
            plugin2.to_caddy(),
            "\tplugin2 arg1 arg2 {\n\t\tprop1 arg1\n\t\tprop2\n\t}"
        )

    def test_plugin_eq(self):
        plugin1 = CoreDNSPlugin("plugin1", "arg1", "arg2")
        plugin2 = CoreDNSPlugin("plugin2", "arg1", "arg2")
        plugin3 = CoreDNSPlugin("plugin1", "arg1", "arg2", properties={
            "prop1": CoreDNSPluginProperty("prop1", "arg1")
        })
        plugin4 = CoreDNSPlugin("plugin1", "arg1", "arg2", properties={
            "prop1": CoreDNSPluginProperty("prop1", "arg1")
        })
        plugin5 = CoreDNSPlugin("plugin1", "arg1", "arg2", properties={
            "prop2": CoreDNSPluginProperty("prop1", "arg1")
        })
        plugin6 = CoreDNSPlugin("plugin1", "arg1", "arg2", properties={
            "prop1": CoreDNSPluginProperty("prop1")
        })

        self.assertFalse(plugin1 == plugin2)
        self.assertFalse(plugin1 == plugin3)

        self.assertTrue(plugin3 == plugin4)
        self.assertFalse(plugin3 == plugin5)
        self.assertFalse(plugin3 == plugin6)

    def test_plugin_add_property_from_instance_replace(self):
        prop1 = CoreDNSPluginProperty("prop1", "arg1", "arg2")
        prop2 = CoreDNSPluginProperty("prop1")

        plugin = CoreDNSPlugin("plugin", "arg1")
        self.assertEqual(plugin.add_object(prop1), prop1)
        self.assertDictEqual(plugin.objects, {
            "prop1": CoreDNSPluginProperty("prop1", "arg1", "arg2")
        })
        self.assertEqual(plugin.add_object(prop2), prop2)
        self.assertDictEqual(plugin.objects, {
            "prop1": CoreDNSPluginProperty("prop1")
        })

    def test_plugin_add_property_from_instance_no_replace(self):
        prop1 = CoreDNSPluginProperty("prop1", "arg1", "arg2")
        prop2 = CoreDNSPluginProperty("prop1")

        plugin = CoreDNSPlugin("plugin", "arg1")
        self.assertEqual(plugin.add_object(prop1, replace=False), prop1)
        self.assertDictEqual(plugin.objects, {
            "prop1": CoreDNSPluginProperty("prop1", "arg1", "arg2")
        })
        self.assertIsNone(plugin.add_object(prop2, replace=False))
        self.assertDictEqual(plugin.objects, {
            "prop1": CoreDNSPluginProperty("prop1", "arg1", "arg2")
        })

    def test_plugin_add_property(self):
        prop = CoreDNSPluginProperty("prop1", "arg1", "arg2")
        plugin = CoreDNSPlugin("plugin")
        self.assertEqual(
            plugin.add_property("prop1", "arg1", "arg2"),
            prop
        )
        self.assertDictEqual(plugin.objects, {"prop1": prop})

    def test_plugin_remove_property(self):
        prop1 = CoreDNSPluginProperty("prop1", "arg1")
        prop2 = CoreDNSPluginProperty("prop2")
        plugin = CoreDNSPlugin("plugin", properties={
            "prop1": prop1,
            "prop2": prop2
        })

        self.assertIsNone(plugin.remove_object("prop3"))
        self.assertEqual(plugin.remove_object("prop1"), prop1)
        self.assertIsNone(plugin.remove_object("prop1"))
        self.assertEqual(plugin.remove_object("prop2"), prop2)
        self.assertIsNone(plugin.remove_object("prop2"))

    def test_plugin_to_dict(self):
        plugin = CoreDNSPlugin("plugin", "arg1", "arg2", properties={
            "prop1": CoreDNSPluginProperty("prop1", "arg1"),
            "prop2": CoreDNSPluginProperty("prop2", "arg1", "arg2")
        })

        self.assertDictEqual(plugin.to_dict(), {
            "depth": 1,
            "name": "plugin",
            "name_string": "plugin",
            "args": ["arg1", "arg2"],
            "objects": {
                "prop1": {
                    "depth": 2,
                    "name": "prop1",
                    "name_string": "prop1",
                    "args": ["arg1"],
                    "objects": {}
                },
                "prop2": {
                    "depth": 2,
                    "name": "prop2",
                    "name_string": "prop2",
                    "args": ["arg1", "arg2"],
                    "objects": {}
                },
            }
        })

    def test_plugin_from_dict(self):
        plugin = CoreDNSPlugin.from_dict({
            "name": "plugin",
            "args": ["arg1", "arg2"],
            "objects": {
                "prop1": {
                    "name": "prop1",
                    "args": ["arg1"]
                },
                "prop2": {
                    "name": "prop2",
                    "args": ["arg1", "arg2"]
                }
            }
        })

        self.assertEqual(
            plugin,
            CoreDNSPlugin("plugin", "arg1", "arg2", properties={
                "prop1": CoreDNSPluginProperty("prop1", "arg1"),
                "prop2": CoreDNSPluginProperty("prop2", "arg1", "arg2")
            })
        )

    # CoreDNSZone tests
    def test_zone_init_no_raise_no_plugins(self):
        try:
            zone1 = CoreDNSZone("zone1")
            zone2 = CoreDNSZone("zone2", port=69)
        except ValueError:
            self.fail("CoreDNSZone.__init__ raised ValueError")

        self.assertEqual(zone1.port, 53)
        self.assertEqual(zone2.port, 69)

        self.assertDictEqual(zone1.objects, {})
        self.assertDictEqual(zone2.objects, {})

    def test_zone_init_no_raise_plugins(self):
        plugin1 = CoreDNSPlugin("plugin1", "arg1")
        plugin2 = CoreDNSPlugin("plugin1", properties={
            "prop1": CoreDNSPluginProperty("prop1", "arg1")
        })

        try:
            zone1 = CoreDNSZone("zone1", plugins={
                "plugin1": plugin1
            })
            zone2 = CoreDNSZone("zone2", port=69, plugins={
                "plugin1": plugin2
            })
        except ValueError:
            self.fail("CoreDNSZone.__init__ raised ValueError")

        self.assertEqual(zone1.port, 53)
        self.assertEqual(zone2.port, 69)

        self.assertDictEqual(zone1.objects, {
            "plugin1": plugin1
        })
        self.assertDictEqual(zone2.objects, {
            "plugin1": plugin2
        })

    def test_zone_init_raise(self):
        self.assertRaises(ValueError, CoreDNSZone, "zone", -1)
        self.assertRaises(ValueError, CoreDNSZone, "zone", -2, {
            "plugin1": CoreDNSPlugin("plugin1")
        })

    def test_zone_to_caddy(self):
        zone1 = CoreDNSZone("zone1")
        zone2 = CoreDNSZone("zone2", 69)
        zone3 = CoreDNSZone("zone3", 69, {
            "plugin1": CoreDNSPlugin("plugin1", "arg1"),
            "plugin2": CoreDNSPlugin("plugin2", "arg2", properties={
                "prop1": CoreDNSPluginProperty("prop1", "arg1"),
                "prop2": CoreDNSPluginProperty("prop2")
            })
        })

        self.assertEqual(zone1.to_caddy(), "zone1:53")
        self.assertEqual(zone2.to_caddy(), "zone2:69")
        self.assertEqual(
            zone3.to_caddy(),
            "zone3:69 {\n"
            "\tplugin1 arg1\n"
            "\tplugin2 arg2 {\n"
            "\t\tprop1 arg1\n"
            "\t\tprop2\n"
            "\t}\n"
            "}"
        )

    def test_zone_eq(self):
        zone1 = CoreDNSZone("zone1")
        zone2 = CoreDNSZone("zone1", 69)
        zone3 = CoreDNSZone("zone1", 69, {
            "plugin1": CoreDNSPlugin("plugin1")
        })
        zone4 = CoreDNSZone("zone1", 69, {
            "plugin1": CoreDNSPlugin("plugin1"),
            "plugin2": CoreDNSPlugin("plugin2")
        })
        zone5 = CoreDNSZone("zone1", 69, {
            "plugin1": CoreDNSPlugin("plugin1"),
            "plugin2": CoreDNSPlugin("plugin2")
        })
        zone6 = CoreDNSZone("zone2")
        zone7 = CoreDNSZone("zone1", 69, {
            "plugin2": CoreDNSPlugin("plugin2"),
            "plugin3": CoreDNSPlugin("plugin3")
        })
        zone8 = CoreDNSZone("zone1", 69, {
            "plugin2": CoreDNSPlugin("plugin2"),
            "plugin1": CoreDNSPlugin("plugin1")
        })
        zone9 = CoreDNSZone("zone1", 69, {
            "plugin1": CoreDNSPlugin("plugin2"),
            "plugin2": CoreDNSPlugin("plugin3")
        })

        self.assertFalse(zone1 == zone2)
        self.assertFalse(zone1 == zone6)
        self.assertFalse(zone2 == zone3)
        self.assertFalse(zone3 == zone4)
        self.assertTrue(zone4 == zone5)
        self.assertTrue(zone4 == zone8)
        self.assertFalse(zone4 == zone7)
        self.assertFalse(zone4 == zone9)

    def test_zone_add_plugin_from_instance_replace(self):
        plugin1 = CoreDNSPlugin("plugin1", "arg1")
        plugin2 = CoreDNSPlugin("plugin1")

        zone = CoreDNSZone("zone")
        self.assertEqual(
            zone.add_object(plugin1),
            plugin1
        )
        self.assertDictEqual(zone.objects, {
            "plugin1": plugin1
        })
        self.assertEqual(
            zone.add_object(plugin2),
            plugin2
        )
        self.assertDictEqual(zone.objects, {
            "plugin1": plugin2
        })

    def test_zone_add_plugin_from_instance_no_replace(self):
        plugin1 = CoreDNSPlugin("plugin1", "arg1")
        plugin2 = CoreDNSPlugin("plugin1")

        zone = CoreDNSZone("zone")
        self.assertEqual(zone.add_object(plugin1, replace=False), plugin1)
        self.assertDictEqual(zone.objects, {"plugin1": plugin1})
        self.assertIsNone(zone.add_object(plugin2, replace=False))
        self.assertDictEqual(zone.objects, {"plugin1": plugin1})

    def test_zone_add_plugin(self):
        zone = CoreDNSZone("zone")
        plugin1 = CoreDNSPlugin("plugin1", "arg1")
        plugin2 = CoreDNSPlugin("plugin2", "arg1", properties={
            "prop1": CoreDNSPluginProperty("prop1"),
            "prop2": CoreDNSPluginProperty("prop2", "arg1")
        })

        self.assertEqual(
            zone.add_plugin("plugin1", "arg1"),
            plugin1
        )
        self.assertDictEqual(zone.objects, {"plugin1": plugin1})

        self.assertEqual(
            zone.add_plugin("plugin2", "arg1", properties={
                "prop1": CoreDNSPluginProperty("prop1"),
                "prop2": CoreDNSPluginProperty("prop2", "arg1")
            }),
            plugin2
        )
        self.assertDictEqual(zone.objects, {
            "plugin1": plugin1,
            "plugin2": plugin2
        })

    def test_zone_remove_plugin(self):
        plugin1 = CoreDNSPlugin("plugin1", "arg1")
        plugin2 = CoreDNSPlugin("plugin2", "arg1", properties={
            "prop1": CoreDNSPluginProperty("prop1"),
            "prop2": CoreDNSPluginProperty("prop2", "arg1")
        })
        zone = CoreDNSZone("zone", plugins={
            "plugin1": plugin1,
            "plugin2": plugin2
        })

        self.assertIsNone(zone.remove_object("plugin3"))
        self.assertEqual(zone.remove_object("plugin1"), plugin1)
        self.assertIsNone(zone.remove_object("plugin1"))
        self.assertDictEqual(zone.objects, {"plugin2": plugin2})
        self.assertEqual(zone.remove_object("plugin2"), plugin2)
        self.assertIsNone(zone.remove_object("plugin2"))
        self.assertDictEqual(zone.objects, {})

    def test_zone_to_dict(self):
        zone = CoreDNSZone("zone", plugins={
            "plugin1": CoreDNSPlugin("plugin1", "arg1"),
            "plugin2": CoreDNSPlugin("plugin2", "arg1", properties={
                "prop1": CoreDNSPluginProperty("prop1"),
                "prop2": CoreDNSPluginProperty("prop2", "arg1")
            })
        })

        self.assertDictEqual(zone.to_dict(), {
            "depth": 0,
            "name": "zone",
            "port": 53,
            "name_string": "zone:53",
            "args": [],
            "objects": {
                "plugin1": {
                    "depth": 1,
                    "name": "plugin1",
                    "name_string": "plugin1",
                    "args": ["arg1"],
                    "objects": {}
                },
                "plugin2": {
                    "depth": 1,
                    "name": "plugin2",
                    "name_string": "plugin2",
                    "args": ["arg1"],
                    "objects": {
                        "prop1": {
                            "depth": 2,
                            "name": "prop1",
                            "name_string": "prop1",
                            "args": [],
                            "objects": {}
                        },
                        "prop2": {
                            "depth": 2,
                            "name": "prop2",
                            "name_string": "prop2",
                            "args": ["arg1"],
                            "objects": {}
                        },
                    }
                },
            }
        })

    def test_zone_from_dict(self):
        zone = CoreDNSZone.from_dict({
            "name": "zone",
            "port": 53,
            "objects": {
                "plugin1": {
                    "name": "plugin1",
                    "args": ["arg1"],
                    "objects": {}
                },
                "plugin2": {
                    "name": "plugin2",
                    "args": ["arg1"],
                    "objects": {
                        "prop1": {
                            "name": "prop1",
                            "args": []
                        },
                        "prop2": {
                            "name": "prop2",
                            "args": ["arg1"]
                        }
                    }
                }
            }
        })

        self.assertEqual(zone, CoreDNSZone("zone", plugins={
            "plugin1": CoreDNSPlugin("plugin1", "arg1"),
            "plugin2": CoreDNSPlugin("plugin2", "arg1", properties={
                "prop1": CoreDNSPluginProperty("prop1"),
                "prop2": CoreDNSPluginProperty("prop2", "arg1")
            })
        }))

    # CoreDNSCorefile tests
    def test_corefile_init_no_raise(self):
        try:
            corefile = CoreDNSCorefile({
                ".": CoreDNSZone(".")
            })
        except ValueError:
            self.fail("CoreDNSCorefile.__init__ raised ValueError")

        self.assertDictEqual(corefile.objects, {".": CoreDNSZone(".")})

    def test_corefile_init_raise(self):
        self.assertRaises(ValueError, CoreDNSCorefile, {})

    def test_corefile_to_caddy(self):
        corefile1 = CoreDNSCorefile({".": CoreDNSZone(".")})
        corefile2 = CoreDNSCorefile({
            ".": CoreDNSZone(".", plugins={
                "plugin1": CoreDNSPlugin("plugin1", "arg1"),
            })
        })
        corefile3 = CoreDNSCorefile({
            ".": CoreDNSZone(".", plugins={
                "plugin1": CoreDNSPlugin("plugin1", "arg1", properties={
                    "prop1": CoreDNSPluginProperty("prop1", "arg1"),
                    "prop2": CoreDNSPluginProperty("prop2")
                }),
                "plugin2": CoreDNSPlugin("plugin2", "arg2", properties={
                    "prop1": CoreDNSPluginProperty("prop1")
                })
            })
        })
        corefile4 = CoreDNSCorefile({
            ".": CoreDNSZone(".", plugins={
                "plugin1": CoreDNSPlugin("plugin1", "arg1", properties={
                    "prop1": CoreDNSPluginProperty("prop1", "arg1"),
                    "prop2": CoreDNSPluginProperty("prop2")
                }),
                "plugin2": CoreDNSPlugin("plugin2", "arg2", properties={
                    "prop1": CoreDNSPluginProperty("prop1")
                })
            }),
            "example.com": CoreDNSZone("example.com", 69, plugins={
                "plugin1": CoreDNSPlugin("plugin1", "arg1", properties={
                    "prop1": CoreDNSPluginProperty("prop1", "arg1"),
                    "prop2": CoreDNSPluginProperty("prop2")
                }),
                "plugin2": CoreDNSPlugin("plugin2", "arg2", properties={
                    "prop1": CoreDNSPluginProperty("prop1")
                })
            })
        })

        self.assertEqual(corefile1.to_caddy(), ".:53")
        self.assertEqual(
            corefile2.to_caddy(),
            ".:53 {\n"
            "\tplugin1 arg1\n"
            "}"
        )
        self.assertEqual(
            corefile3.to_caddy(),
            ".:53 {\n"
            "\tplugin1 arg1 {\n"
            "\t\tprop1 arg1\n"
            "\t\tprop2\n"
            "\t}\n"
            "\tplugin2 arg2 {\n"
            "\t\tprop1\n"
            "\t}\n"
            "}"
        )
        self.assertEqual(
            corefile4.to_caddy(),
            ".:53 {\n"
            "\tplugin1 arg1 {\n"
            "\t\tprop1 arg1\n"
            "\t\tprop2\n"
            "\t}\n"
            "\tplugin2 arg2 {\n"
            "\t\tprop1\n"
            "\t}\n"
            "}\n\n"
            "example.com:69 {\n"
            "\tplugin1 arg1 {\n"
            "\t\tprop1 arg1\n"
            "\t\tprop2\n"
            "\t}\n"
            "\tplugin2 arg2 {\n"
            "\t\tprop1\n"
            "\t}\n"
            "}"
        )

    def test_corefile_eq(self):
        corefile1 = CoreDNSCorefile({".": CoreDNSZone(".")})
        corefile2 = CoreDNSCorefile({
            ".": CoreDNSZone("."),
            "example.io": CoreDNSZone("example.io", 69)
        })
        corefile3 = CoreDNSCorefile({
            ".": CoreDNSZone("."),
            "example.io": CoreDNSZone("example.io", 69)
        })
        corefile4 = CoreDNSCorefile({
            ".": CoreDNSZone("."),
            "example.com": CoreDNSZone("example.com", 69)
        })
        corefile5 = CoreDNSCorefile({
            ".": CoreDNSZone("."),
            "example.io": CoreDNSZone("example.io", 420)
        })

        self.assertFalse(corefile1 == corefile2)
        self.assertTrue(corefile2 == corefile3)
        self.assertFalse(corefile3 == corefile4)
        self.assertFalse(corefile3 == corefile5)

    def test_corefile_add_zone_from_instance_replace(self):
        corefile = CoreDNSCorefile(zones={
            ".": CoreDNSZone(".")
        })
        zone1 = CoreDNSZone(".", 69)
        zone2 = CoreDNSZone(".", 69, plugins={"plugin1": CoreDNSPlugin("plugin1")})

        self.assertEqual(corefile.add_object(zone1), zone1)
        self.assertDictEqual(corefile.objects, {".": zone1})

        self.assertEqual(corefile.add_object(zone2), zone2)
        self.assertDictEqual(corefile.objects, {".": zone2})

    def test_corefile_add_zone_from_instance_no_replace(self):
        root_zone = CoreDNSZone(".")
        zone1 = CoreDNSZone("example.com", 69)
        zone2 = CoreDNSZone("example.com", 69, plugins={"plugin1": CoreDNSPlugin("plugin1")})
        corefile = CoreDNSCorefile(zones={
            ".": root_zone
        })

        self.assertEqual(corefile.add_object(zone1, False), zone1)
        self.assertDictEqual(corefile.objects, {
            ".": root_zone,
            "example.com": zone1
        })

        self.assertIsNone(corefile.add_object(zone2, False))
        self.assertDictEqual(corefile.objects, {
            ".": root_zone,
            "example.com": zone1
        })

    def test_corefile_add_zone(self):
        root_zone = CoreDNSZone(".")
        corefile = CoreDNSCorefile(zones={
            ".": root_zone
        })
        zone1 = CoreDNSZone("example.com", 69)

        self.assertEqual(
            corefile.add_zone("example.com", 69),
            zone1
        )
        self.assertDictEqual(corefile.objects, {
            ".": root_zone,
            "example.com": zone1
        })

    def test_corefile_remove_zone(self):
        corefile = CoreDNSCorefile(zones={
            ".": CoreDNSZone("."),
            "example.com": CoreDNSZone("example.com"),
            "example.io": CoreDNSZone("example.io", 69)
        })

        self.assertIsNone(corefile.remove_object("example.org"))
        self.assertEqual(
            corefile.remove_object("example.com"),
            CoreDNSZone("example.com")
        )
        self.assertDictEqual(corefile.objects, {
            ".": CoreDNSZone("."),
            "example.io": CoreDNSZone("example.io", 69)
        })
        self.assertIsNone(corefile.remove_object("example.com"))
        self.assertEqual(
            corefile.remove_object("example.io"),
            CoreDNSZone("example.io", 69)
        )
        self.assertDictEqual(corefile.objects, {".": CoreDNSZone(".")})

    def test_corefile_to_dict(self):
        zone1 = CoreDNSZone("zone1", plugins={
            "plugin1": CoreDNSPlugin("plugin1", "arg1")
        })
        zone2 = CoreDNSZone("zone2", plugins={
            "plugin1": CoreDNSPlugin("plugin1", "arg1", properties={
                "prop1": CoreDNSPluginProperty("prop1"),
            })
        })
        corefile = CoreDNSCorefile(zones={"zone1": zone1, "zone2": zone2})

        self.assertDictEqual(corefile.to_dict(), {
            "zone1": {
                "depth": 0,
                "name": "zone1",
                "port": 53,
                "name_string": "zone1:53",
                "args": [],
                "objects": {
                    "plugin1": {
                        "depth": 1,
                        "name": "plugin1",
                        "name_string": "plugin1",
                        "args": ["arg1"],
                        "objects": {}
                    }
                }
            },
            "zone2": {
                "depth": 0,
                "name": "zone2",
                "port": 53,
                "name_string": "zone2:53",
                "args": [],
                "objects": {
                    "plugin1": {
                        "depth": 1,
                        "name": "plugin1",
                        "name_string": "plugin1",
                        "args": ["arg1"],
                        "objects": {
                            "prop1": {
                                "depth": 2,
                                "name": "prop1",
                                "name_string": "prop1",
                                "args": [],
                                "objects": {}
                            }
                        }
                    }
                }
            }
        })

    def test_corefile_from_dict(self):
        corefile = CoreDNSCorefile.from_dict({
            "zone1": {
                "name": "zone1",
                "port": 53,
                "objects": {
                    "plugin1": {
                        "name": "plugin1",
                        "args": ["arg1"],
                        "objects": {}
                    }
                }
            },
            "zone2": {
                "name": "zone2",
                "port": 53,
                "objects": {
                    "plugin1": {
                        "name": "plugin1",
                        "args": ["arg1"],
                        "objects": {
                            "prop1": {
                                "name": "prop1",
                                "args": []
                            }
                        }
                    }
                }
            }
        })

        self.assertEqual(corefile, CoreDNSCorefile(zones={
            "zone1": CoreDNSZone("zone1", plugins={
                "plugin1": CoreDNSPlugin("plugin1", "arg1")
            }),
            "zone2": CoreDNSZone("zone2", plugins={
                "plugin1": CoreDNSPlugin("plugin1", "arg1", properties={
                    "prop1": CoreDNSPluginProperty("prop1")
                })
            })
        }))
