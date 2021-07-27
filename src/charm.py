#!/usr/bin/env python3
# Copyright 2021 umtdg
# See LICENSE file for licensing details.

import logging

from ops.charm import (
    CharmBase,
    ActionEvent
)
from ops.main import main
from ops.framework import StoredState
from ops.model import (
    ActiveStatus,
    ModelError,
    BlockedStatus,
    MaintenanceStatus
)
from ops.pebble import PathError

from coredns import (
    CoreDNSCorefile,
    CoreDNSZone,
    PLUGIN_LOG,
    PLUGIN_ERRORS,
    PLUGIN_CACHE,
    PLUGIN_FORWARD_CLOUDFLARE
)
from dnszonefile import CoreDNSZoneFile
from parser import (
    Parser,
    PARSER_COMMANDS,
    ValidationError,
    RequiredError
)


logger = logging.getLogger(__name__)

ACTION_RESULT_NO_REPLACE = {"result": "Not replacing, nothing changed"}
ACTION_RESULT_REMOVE_NOT_FOUND = {"result": "Not found, nothing changed"}


# TODO: Add functions to handle actions
# TODO: Default Corefile
class CorednsK8SCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)

        # Pebble hooks
        self.framework.observe(self.on.coredns_pebble_ready, self._on_coredns_pebble_ready)

        # Basic hooks

        # Action hooks
        self.framework.observe(self.on.add_property_action, self._on_add_property)
        self.framework.observe(self.on.remove_property_action, self._on_remove_property)
        self.framework.observe(self.on.add_plugin_action, self._on_add_plugin)
        self.framework.observe(self.on.remove_plugin_action, self._on_remove_plugin)
        self.framework.observe(self.on.add_zone_action, self._on_add_zone)
        self.framework.observe(self.on.remove_zone_action, self._on_remove_zone)
        self.framework.observe(self.on.print_corefile_action, self._on_print_corefile)
        self.framework.observe(self.on.print_zone_action, self._on_print_zone)
        # self.framework.observe(self.on.print_zonefile_action, self._on_print_zonefile)
        self.framework.observe(self.on.update_action, self._on_update)

        self._default_corefile = CoreDNSCorefile(
            {
                ".": CoreDNSZone(".", 53, {
                    "forward": PLUGIN_FORWARD_CLOUDFLARE,
                    "log": PLUGIN_LOG,
                    "errors": PLUGIN_ERRORS,
                    "cache": PLUGIN_CACHE
                })
            }
        ).to_dict()

        self._stored.set_default(
            corefile=self._default_corefile,
            new_corefile=self._default_corefile,
            zonefiles={}
        )

    @property
    def corefile(self):
        return CoreDNSCorefile.from_dict(self._stored.corefile)

    @property
    def new_corefile(self):
        return CoreDNSCorefile.from_dict(self._stored.new_corefile)

    def parse_actions_file(self):
        corefile = self.corefile

        try:
            actions_file = self.model.resources.fetch("script-file")
            Parser.exec(corefile, actions_file)
        except ModelError:
            self.unit.status = MaintenanceStatus(
                "Resource 'script-file' not found. Using default Corefile"
            )
            corefile = CoreDNSCorefile.from_dict(self._default_corefile)
        except RequiredError as e:
            self.unit.status = MaintenanceStatus(
                "Errors occurred while reading actions file:"
                " {}. Using default Corefile".format(
                    e.message
                )
            )
            corefile = CoreDNSCorefile.from_dict(self._default_corefile)

        self._stored.corefile = corefile.to_dict()
        self._stored.new_corefile = self._stored.corefile

    def _on_coredns_pebble_ready(self, event):
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload

        self.parse_actions_file()

        try:
            container.push("/Corefile", self.corefile.to_caddy())
        except PathError as e:
            self.unit.status = BlockedStatus(
                f"Failed to create /Corefile: Message: {e.message}"
            )

        pebble_layer = {
            "summary": "coredns layer",
            "description": "pebble config layer for coredns",
            "services": {
                "coredns": {
                    "override": "replace",
                    "summary": "coredns",
                    "command": "/coredns -conf /Corefile",
                    "startup": "enabled",
                }
            },
        }
        container.add_layer("coredns", pebble_layer, combine=True)

        container.autostart()

        self.unit.status = ActiveStatus("Pebble ready")

    def _on_print_corefile(self, event: ActionEvent):
        current: bool = event.params["current"]

        event.log("Outputting {} Corefile".format("current" if current else "new"))

        corefile = self.corefile if current else self.new_corefile
        print(corefile.to_caddy())

    def _on_print_zone(self, event: ActionEvent):
        zone: str = event.params["zone"]
        current: bool = event.params["current"]

        corefile = self.corefile if current else self.new_corefile
        event.log("Outputting zone from {} corefile".format(
            "current" if current else "new"
        ))
        if zone not in corefile.objects:
            event.fail(f"Could not found zone {zone}")
        else:
            print(corefile.objects[zone].to_caddy())

    def _on_print_zonefile(self, event: ActionEvent):
        zonefile: str = event.params["zonefile"]

        event.log("Outputting zone file")
        if zonefile in self._stored.zonefiles:
            print(CoreDNSZoneFile.from_dict(self._stored.zonefiles[zonefile]).to_caddy())
        else:
            event.fail(f"Zone file {zonefile} not found")

    def _add_remove_action(
            self,
            func: str,
            event: ActionEvent,
            msg: str
    ):
        event.log(msg)

        corefile = self.new_corefile

        try:
            if "args" in event.params:
                event.params["args"] = event.params["args"].split()
            result = PARSER_COMMANDS[func](corefile, event.params)

            event.set_results({"result": result})

            self._stored.new_corefile = corefile.to_dict()
        except ValidationError as e:
            event.fail(e.message)

    def _on_add_property(self, event: ActionEvent):
        self._add_remove_action(
            "add_property",
            event,
            "Adding property"
        )

    def _on_remove_property(self, event: ActionEvent):
        self._add_remove_action(
            "remove_property",
            event,
            "Removing property"
        )

    def _on_add_plugin(self, event: ActionEvent):
        self._add_remove_action(
            "add_plugin",
            event,
            "Adding plugin"
        )

    def _on_remove_plugin(self, event: ActionEvent):
        self._add_remove_action(
            "remove_plugin",
            event,
            "Removing plugin"
        )

    def _on_add_zone(self, event: ActionEvent):
        self._add_remove_action(
            "add_zone",
            event,
            "Adding zone"
        )

    def _on_remove_zone(self, event: ActionEvent):
        self._add_remove_action(
            "remove_zone",
            event,
            "Removing zone"
        )

    def _on_update(self, event: ActionEvent):
        new_corefile = self.new_corefile

        if self.corefile == new_corefile:
            event.set_results({"result": "Corefile not changed, nothing to do"})
        else:
            self.unit.status = MaintenanceStatus("Updating Corefile")

            container = self.unit.get_container("coredns")

            # Update stored Corefile and update on disk
            self._stored.corefile = new_corefile.to_dict()
            try:
                container.push("/Corefile", new_corefile.to_caddy())
            except PathError as e:
                self.unit.status = BlockedStatus(
                    "Failed to create /Corefile: Kind: {}, Message: {}".format(
                        e.kind,
                        e.message
                    )
                )

            event.log("Stopping container: coredns")
            container.stop("coredns")
            event.log("Starting container: coredns")
            container.autostart()

            self.unit.status = ActiveStatus("Ready")


if __name__ == "__main__":
    main(CorednsK8SCharm)
