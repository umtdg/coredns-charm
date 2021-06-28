# Copyright 2021 umtdg
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest
from unittest.mock import (
    # Mock,
    MagicMock
)

from charm import CorednsK8SCharm
from ops.model import ActiveStatus
from ops.testing import Harness


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(CorednsK8SCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()
        container = self.harness.model.unit.get_container("coredns")
        container.push = MagicMock()
        container.stop = MagicMock()
        container.start = MagicMock()

    # def test_action(self):
    #     # the harness doesn't (yet!) help much with actions themselves
    #     action_event = Mock(params={"fail": ""})
    #     self.harness.charm._on_fortune_action(action_event)
    #
    #     self.assertTrue(action_event.set_results.called)
    #
    # def test_action_fail(self):
    #     action_event = Mock(params={"fail": "fail this"})
    #     self.harness.charm._on_fortune_action(action_event)
    #
    #     self.assertEqual(action_event.fail.call_args, [("fail this",)])

    def test_coredns_pebble_ready(self):
        initial_plan = self.harness.get_container_pebble_plan("coredns")
        self.assertEqual(initial_plan.to_yaml(), "{}\n")

        expected_plan = {
            "services": {
                "coredns": {
                    "override": "replace",
                    "summary": "coredns",
                    "command": "/coredns -conf /Corefile",
                    "startup": "enabled",
                }
            },
        }
        container = self.harness.model.unit.get_container("coredns")
        self.harness.charm.on.coredns_pebble_ready.emit(container)
        updated_plan = self.harness.get_container_pebble_plan("coredns").to_dict()

        self.assertEqual(expected_plan, updated_plan)

        service = self.harness.model.unit.get_container(
            "coredns"
        ).get_service("coredns")
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, ActiveStatus("Pebble ready"))
