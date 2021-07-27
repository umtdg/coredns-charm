import unittest

from typing import (
    Type,
    Callable
)

from parser import (
    RequiredError,
    ValidationError,
    Parser,
    ResultType
)

from coredns import (
    CoreDNSCorefile,
    CoreDNSZone,
    CoreDNSPlugin,
    CoreDNSPluginProperty,
    PLUGIN_ERRORS,
    PLUGIN_CACHE,
    PLUGIN_FORWARD_CLOUDFLARE,
    PLUGIN_LOG
)


class TestParser(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None

    # Test custom exceptions

    def myAssertRaises(self, ex: Type[BaseException]):
        def _raise(e):
            raise e

        self.assertRaises(ex, lambda: _raise(ex()))

    def myAssertNotRaises(self, ex: Type[BaseException], f: Callable, *args, **kwargs):
        try:
            f(*args, **kwargs)
        except ex as e:
            self.fail(f"{f.__name__} raised {ex.__name__} unexpectedly: {e.message}")

    def test_validation_error(self):
        self.myAssertRaises(ValidationError)

    def test_required_error(self):
        self.myAssertRaises(RequiredError)

    def test_str2bool(self):
        self.assertTrue(Parser.str2bool("true"))
        self.assertTrue(Parser.str2bool("tRuE"))
        self.assertTrue(Parser.str2bool("yes"))
        self.assertTrue(Parser.str2bool("yEs"))

    def test_convert_params(self):
        default = {
            "args": "arg1 arg2",
            "port": "69",
            "replace": "yes"
        }

        params = dict(default)
        Parser.convert_params(params, {
            "args": str.split,
            "port": int
        })
        self.assertListEqual(params["args"], ["arg1", "arg2"])
        self.assertEqual(params["port"], 69)
        self.assertEqual(params["replace"], "yes")

        params = dict(default)
        Parser.convert_params(params)
        self.assertListEqual(params["args"], ["arg1", "arg2"])
        self.assertEqual(params["port"], 69)
        self.assertEqual(params["replace"], True)

    def test_default_params(self):
        params = {
            "args": ["arg1", "arg2"]
        }

        defaults = {
            "replace": "yes",
            "port": "53"
        }

        Parser.default_params(params, defaults, convert=True, conversion_map={
            "replace": bool,
            "port": int
        })

        self.assertListEqual(params["args"], ["arg1", "arg2"])
        self.assertEqual(params["replace"], True)
        self.assertEqual(params["port"], 53)

    def test_parse_args(self):
        cmd1 = "name=fallthrough args='in-addr.arpa ip6.arpa' zone=. plugin=kubernetes"
        cmd2 = "name=pods zone=. plugin=kubernetes"
        cmd3 = "name=pods zone=. plugin=kubernetes replace=no"

        self.assertDictEqual(Parser.parse_args(cmd1), {
            "name": "fallthrough",
            "args": ["in-addr.arpa", "ip6.arpa"],
            "zone": ".",
            "plugin": "kubernetes",
            "replace": True
        })
        self.assertDictEqual(Parser.parse_args(cmd2), {
            "name": "pods",
            "zone": ".",
            "plugin": "kubernetes",
            "args": [],
            "replace": True
        })
        self.assertDictEqual(Parser.parse_args(cmd3), {
            "name": "pods",
            "zone": ".",
            "plugin": "kubernetes",
            "args": [],
            "replace": False
        })

    def test_reset(self):
        corefile = CoreDNSCorefile(zones={
            ".": CoreDNSZone(".")
        })
        self.assertDictEqual(corefile.objects, {
            ".": CoreDNSZone(".")
        })

        Parser.reset(corefile)
        self.assertDictEqual(corefile.objects, {})

    def test_return_result_if_none(self):
        self.assertEqual(
            Parser.return_result_if_none(None, ResultType.REMOVE_NOT_FOUND),
            "Not found, nothing changed"
        )
        self.assertEqual(
            Parser.return_result_if_none(
                CoreDNSPlugin("plugin"),
                ResultType.ADD_NO_REPLACE
            ),
            "\tplugin"
        )

    def test_raise_required(self):
        given = {
            "name": "name",
            "zone": "zone"
        }
        required = ["name", "zone", "plugin"]

        self.assertRaises(
            RequiredError,
            Parser.raise_required,
            given,
            required
        )

        given["plugin"] = "plugin"
        self.myAssertNotRaises(
            RequiredError,
            Parser.raise_required,
            given,
            required
        )

    def test_validate_plugin_owners(self):
        corefile = CoreDNSCorefile(zones={
            ".": CoreDNSZone(".")
        })
        self.myAssertNotRaises(
            ValidationError,
            Parser.validate_plugin_owners,
            corefile,
            "."
        )

        self.assertRaises(
            ValidationError,
            Parser.validate_plugin_owners,
            corefile,
            "example.io"
        )

    def test_validate_property_owners(self):
        corefile = CoreDNSCorefile(zones={
            ".": CoreDNSZone(".", plugins={
                "plugin": CoreDNSPlugin("plugin")
            })
        })
        self.myAssertNotRaises(
            ValidationError,
            Parser.validate_property_owners,
            corefile,
            "plugin",
            "."
        )

        self.assertRaises(
            ValidationError,
            Parser.validate_property_owners,
            corefile,
            "plug",
            "."
        )
        self.assertRaises(
            ValidationError,
            Parser.validate_property_owners,
            corefile,
            "plugin",
            "example.io"
        )

    def test_exec_no_raise(self):
        filename = "tests/test_script.txt"
        corefile = CoreDNSCorefile(
            {
                ".": CoreDNSZone(".", 53, {
                    "forward": PLUGIN_FORWARD_CLOUDFLARE,
                    "log": PLUGIN_LOG,
                    "errors": PLUGIN_ERRORS,
                    "cache": PLUGIN_CACHE
                })
            }
        )

        Parser.exec(corefile, filename)
        self.assertTrue(corefile == CoreDNSCorefile(
            zones={
                ".": CoreDNSZone(".", plugins={
                    "forward": PLUGIN_FORWARD_CLOUDFLARE,
                    "log": PLUGIN_LOG,
                    "errors": PLUGIN_ERRORS,
                    "cache": PLUGIN_CACHE,
                    "kubernetes": CoreDNSPlugin(
                        "kubernetes", "cluster.local", "in-addr.arpa", "ip6.arpa",
                        properties={
                            "fallthrough": CoreDNSPluginProperty(
                                "fallthrough", "in-addr.arpa", "ip6.arpa"
                            ),
                            "pods": CoreDNSPluginProperty("pods", "insecure")
                        }
                    )
                }),
                "example.io": CoreDNSZone("example.io", port=69, plugins={
                    "log": PLUGIN_LOG,
                    "errors": PLUGIN_ERRORS
                })
            }
        ))

    def test_exec_raise(self):
        filename = "tests/test_script_unknown_command.txt"
        corefile = CoreDNSCorefile(
            {
                ".": CoreDNSZone(".", 53, {
                    "forward": PLUGIN_FORWARD_CLOUDFLARE,
                    "log": PLUGIN_LOG,
                    "errors": PLUGIN_ERRORS,
                    "cache": PLUGIN_CACHE
                })
            }
        )

        self.assertRaises(RuntimeError, Parser.exec, corefile, filename)
