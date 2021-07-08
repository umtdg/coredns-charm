import unittest

from dnszonefile import (
    DNSRecord,
    CoreDNSZoneFile
)


class TestDNSZoneFile(unittest.TestCase):
    # DNSRecord tests
    def test_dns_record_init(self):
        rec1 = DNSRecord("dns.example.com", "A", "192.168.1.2")
        rec2 = DNSRecord("subdomain.domain.com", "A", "10.69.0.420")
        rec3 = DNSRecord("server.domain.com", "CNAME", "host", "host2")

        self.assertEqual(rec1.hostname, "dns.example.com")
        self.assertEqual(rec1.record_type, "A")
        self.assertListEqual(rec1.args, ["192.168.1.2"])

        self.assertEqual(rec2.hostname, "subdomain.domain.com")
        self.assertEqual(rec2.record_type, "A")
        self.assertListEqual(rec2.args, ["10.69.0.420"])

        self.assertEqual(rec3.hostname, "server.domain.com")
        self.assertEqual(rec3.record_type, "CNAME")
        self.assertListEqual(rec3.args, ["host", "host2"])

    def test_dns_record_to_caddy(self):
        rec1 = DNSRecord("dns.example.com", "A", "192.168.1.2")
        rec2 = DNSRecord("subdomain.domain.com", "A", "10.69.0.420")
        rec3 = DNSRecord("server.domain.com", "CNAME", "host", "host2")

        self.assertEqual(
            rec1.to_caddy(),
            "dns.example.com.\tIN\tA\t192.168.1.2"
        )
        self.assertEqual(
            rec2.to_caddy(),
            "subdomain.domain.com.\tIN\tA\t10.69.0.420"
        )
        self.assertEqual(
            rec3.to_caddy(),
            "server.domain.com.\tIN\tCNAME\thost host2"
        )

    def test_dns_record_eq(self):
        rec1 = DNSRecord("host.example.com", "A", "10.69.0.420")
        rec2 = DNSRecord("host.example.io", "A", "10.69.0.420")
        rec3 = DNSRecord("host.example.com", "A", "10.69.0.420", "10.69.31.420")
        rec4 = DNSRecord("host.example.com", "CNAME", "10.69.0.420")
        rec5 = DNSRecord("host.example.com", "A", "10.69.0.420")
        rec6 = DNSRecord("host.example.com", "A", "10.69.31.420")

        self.assertFalse(rec1 == rec2)
        self.assertFalse(rec1 == rec3)
        self.assertFalse(rec1 == rec4)
        self.assertTrue(rec1 == rec5)
        self.assertFalse(rec1 == rec6)

    def test_dns_record_to_dict(self):
        record = DNSRecord("dns.example.io", "A", "192.168.1.2")

        self.assertDictEqual(record.to_dict(), {
            "hostname": "dns.example.io",
            "record_type": "A",
            "args": ["192.168.1.2"]
        })

    def test_dns_record_from_dict(self):
        record = DNSRecord.from_dict({
            "hostname": "dns.example.io",
            "record_type": "A",
            "args": ["192.168.1.2"]
        })

        self.assertEqual(record, DNSRecord("dns.example.io", "A", "192.168.1.2"))

    # DNSZoneFile tests
    def test_dns_zone_file_init(self):
        zonefile1 = CoreDNSZoneFile()

        self.assertDictEqual(zonefile1.records, {})

    def test_dns_zone_file_add_record_from_instance_replace(self):
        zonefile = CoreDNSZoneFile()
        rec1 = DNSRecord("dns.example.io", "A", "192.168.1.2")
        rec2 = DNSRecord("dns.example.io", "A", "192.168.1.3")

        self.assertEqual(zonefile.add_record_from_instance(rec1), rec1)
        self.assertDictEqual(zonefile.records, {
            "dns.example.io": rec1
        })
        self.assertEqual(zonefile.add_record_from_instance(rec2), rec2)
        self.assertDictEqual(zonefile.records, {
            "dns.example.io": rec2
        })

    def test_dns_zone_file_add_record_from_instance_no_replace(self):
        zonefile = CoreDNSZoneFile()
        rec1 = DNSRecord("dns.example.io", "A", "192.168.1.2")
        rec2 = DNSRecord("dns.example.io", "A", "192.168.1.3")

        self.assertEqual(zonefile.add_record_from_instance(rec1), rec1)
        self.assertDictEqual(zonefile.records, {
            "dns.example.io": rec1
        })
        self.assertIsNone(zonefile.add_record_from_instance(rec2, replace=False))
        self.assertDictEqual(zonefile.records, {
            "dns.example.io": rec1
        })

    def test_dns_zone_file_add_record(self):
        zonefile = CoreDNSZoneFile()
        rec = DNSRecord("dns.example.io", "A", "192.168.1.2")

        self.assertEqual(
            zonefile.add_record(None, "dns.example.io", "A", "192.168.1.2"),
            rec
        )
        self.assertDictEqual(zonefile.records, {
            "dns.example.io": rec
        })

    def test_dns_zone_file_remove_record(self):
        zonefile = CoreDNSZoneFile()
        rec = DNSRecord("dns.example.io", "A", "192.168.1.2")

        zonefile.add_record_from_instance(rec, name="rec")

        self.assertIsNone(zonefile.remove_record("host.example.io"))
        self.assertEqual(zonefile.remove_record("rec"), rec)
        self.assertIsNone(zonefile.remove_record("rec"))
        self.assertDictEqual(zonefile.records, {})

    def test_dns_zone_file_to_caddy(self):
        zonefile = CoreDNSZoneFile()
        zonefile.add_record_from_instance(
            DNSRecord("dns.example.io", "A", "192.168.1.2")
        )

        self.assertEqual(
            zonefile.to_caddy(),
            "dns.example.io.\tIN\tA\t192.168.1.2"
        )

    def test_dns_zone_file_eq(self):
        zonefile1 = CoreDNSZoneFile()

        zonefile2 = CoreDNSZoneFile()
        zonefile2.add_record(None, "dns.example.io", "A", "192.168.1.2")

        zonefile3 = CoreDNSZoneFile()
        zonefile3.add_record(None, "host.example.io", "A", "192.168.1.2")

        zonefile4 = CoreDNSZoneFile()
        zonefile4.add_record(None, "dns.example.io", "A", "192.168.1.3")

        zonefile5 = CoreDNSZoneFile()
        zonefile5.add_record(None, "dns.example.io", "CNAME", "192.168.1.2")

        zonefile6 = CoreDNSZoneFile()
        zonefile6.add_record(None, "dns.example.io", "A", "192.168.1.2")

        self.assertFalse(zonefile1 == zonefile2)
        self.assertFalse(zonefile2 == zonefile3)
        self.assertFalse(zonefile2 == zonefile4)
        self.assertFalse(zonefile2 == zonefile5)
        self.assertTrue(zonefile2 == zonefile6)

    def test_dns_zone_file_to_dict(self):
        zonefile = CoreDNSZoneFile()
        zonefile.add_record("rec1", "dns.example.io", "A", "127.0.0.1")
        zonefile.add_record(None, "host.example.io", "CNAME", "server")

        self.assertDictEqual(zonefile.to_dict(), {
            "rec1": {
                "hostname": "dns.example.io",
                "record_type": "A",
                "args": ["127.0.0.1"]
            },
            "host.example.io": {
                "hostname": "host.example.io",
                "record_type": "CNAME",
                "args": ["server"]
            }
        })

    def test_dns_zone_file_from_dict(self):
        expected = CoreDNSZoneFile()
        expected.add_record("rec1", "dns.example.io", "A", "127.0.0.1")
        expected.add_record(None, "host.example.io", "CNAME", "server")

        zonefile = CoreDNSZoneFile.from_dict({
            "rec1": {
                "hostname": "dns.example.io",
                "record_type": "A",
                "args": ["127.0.0.1"]
            },
            "host.example.io": {
                "hostname": "host.example.io",
                "record_type": "CNAME",
                "args": ["server"]
            }
        })

        self.assertEqual(zonefile, expected)
