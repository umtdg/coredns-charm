from typing import (
    Dict,
    Optional,
    List,
    Union
)
DNSRECORD_DICT_TYPE = Dict[str, Union[str, List[str]]]


class DNSRecord:
    """Class representing a DNS record in DNS zone file"""

    def __init__(
            self,
            hostname: str,
            record_type: str,  # TODO: Use an enumeration instead
            *args: str
    ):
        """Create a DNS record

        Args:
            hostname: First part of the DNS record
            record_type: Type of the DNS record
            *args: Arguments required by the DNS record
        """

        self.hostname: str = hostname
        self.record_type: str = record_type
        self.args: List[str] = list(args)

    def to_caddy(self):
        result = "{}.\tIN\t{}\t{}".format(
            self.hostname,
            self.record_type,
            ' '.join(self.args)
        )
        return result

    def __eq__(self, other: "DNSRecord"):
        if self.record_type != other.record_type:
            return False

        if self.hostname != other.hostname:
            return False

        if len(self.args) != len(other.args):
            return False

        for i in range(len(self.args)):
            if self.args[i] != other.args[i]:
                return False

        return True

    def to_dict(self) -> DNSRECORD_DICT_TYPE:
        return {
            "hostname": self.hostname,
            "record_type": self.record_type,
            "args": self.args
        }

    @staticmethod
    def from_dict(d: DNSRECORD_DICT_TYPE) -> "DNSRecord":
        return DNSRecord(
            d["hostname"],
            d["record_type"],
            *d["args"]
        )


class CoreDNSZoneFile:
    """Class representing a DNS zone file"""

    def __init__(self):
        """Create a DNS zone file"""

        self.records: Dict[str, "DNSRecord"] = {}

    def to_caddy(self):
        return '\n'.join([record.to_caddy() for record in self.records.values()])

    def __eq__(self, other: "CoreDNSZoneFile"):
        if len(self.records) != len(other.records):
            return False

        for key in self.records:
            if key not in other.records:
                return False

            if self.records[key] != other.records[key]:
                return False

        return True

    def to_dict(self) -> Dict[str, DNSRECORD_DICT_TYPE]:
        return {key: self.records[key].to_dict() for key in self.records}

    @staticmethod
    def from_dict(d: Dict[str, DNSRECORD_DICT_TYPE]) -> "CoreDNSZoneFile":
        result = CoreDNSZoneFile()
        for key in d:
            result.add_record_from_instance(DNSRecord.from_dict(d[key]), name=key)
        return result

    def add_record(
            self,
            name: Optional[str],
            hostname: str,
            record_type: str,
            *args: str,
            replace: bool = True
    ) -> Optional[DNSRecord]:
        """Add new record to DNS zone file

        Args:
            name: Name of the record to be added
            hostname: Hostname for the record
            record_type: Type of the record
            *args: Arguments required for the record
            replace: Whether to replace existing record or not

        Returns:
            Return newly added DNSRecord object or
            return None if key is already exists and replace is False
        """

        new_record = DNSRecord(hostname, record_type, *args)
        return self.add_record_from_instance(new_record, name=name, replace=replace)

    def add_record_from_instance(
            self,
            record: DNSRecord,
            name: Optional[str] = None,
            replace: bool = True
    ) -> Optional[DNSRecord]:
        """Add new record to DNS zone file using a DNSRecord instance

        Args:
            record: DNSRecord to add
            name: Save DNS record using this. If None, hostname of the record will be used
            replace: Whether to replace existing record or not

        Returns:
            Return newly added DNSRecord object or
            return None if key is already exists and replace is False
        """

        if name is None:
            name = record.hostname

        if name in self.records:
            if not replace:
                return None

        self.records[name] = record
        return self.records[name]

    def remove_record(self, name: str) -> Optional[DNSRecord]:
        """Remove an existing record from DNS zone file

        Args:
            name: Name of the record to be removed

        Returns:
            If exists, return removed DNSRecord object, return None otherwise
        """

        return self.records.pop(name, None)
