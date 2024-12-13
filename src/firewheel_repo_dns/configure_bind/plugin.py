import os
import pickle
import pprint
import shutil

from dns.dns_objects import DNSServer

from firewheel.control.experiment_graph import AbstractPlugin

CONFIG = {
    "dns_name": "DNS",
    "boilerplate_serial": "2014080800",
    "boilerplate_refresh": "3h",
    "boilerplate_retry": "15M",
    "boilerplate_expire": "3W12h",
    "boilerplate_minimum": "2h20M",
}


class ConfigureBind(AbstractPlugin):
    """This plugin configures DNS for the experiment.

    The plugin walks the graph building zone files for the experiment.
    It then gives the zone files to the DNS server by passing them to
    a vm_resource.

    Graph attributes read:
    name
    interfaces
    type

    Graph attributes set:
    schedule
    """

    def __init__(self, *args, **kwargs):
        """Constructor for ConfigureDNS

        Arguments:
            *args: extra args to pass to AbstractPlugin constructor
            **kwargs: extra keyword args to pass to AbstractPlugin constructor
        """
        super(ConfigureBind, self).__init__(*args, **kwargs)
        self.bind_zones = {}
        self.zonedir = None
        self.dirname = None
        self.DEBUG = False

    def run(self, debug=""):
        """Function to invoke the ConfigureDNS plugin.

        Arguments:
            debug(str): Enable debugging information to see everything the
                parser gathers. Value should be 'True' or 'true' to enable
        """
        self.DEBUG = debug.startswith("T") or debug.startswith("t")

        if self.DEBUG:
            self.dirname = "dns_zones"
            if os.path.exists(self.dirname):
                shutil.rmtree(self.dirname)
            os.mkdir(self.dirname)

        # Create zones for dns servers
        for vertex in self.g.get_vertices():
            # Look for key like {'dns':{"domains" [".ssn.gov"]}}
            if vertex.is_decorated_by(DNSServer):
                name = vertex.name
                if self.DEBUG:
                    self.zonedir = os.path.join(self.dirname, name)
                    os.mkdir(self.zonedir)
                zones = vertex.dns_data.get("zones")
                dns_address = vertex.dns_data.get("dns_address")
                self.generate_zone_files(zones, dns_address)
                pickled_metadata = self.get_metadata(self.bind_zones)
                vertex.add_vm_resource(
                    -2, "configure_bind_agent.py", pickled_metadata, None
                )
                if self.DEBUG:
                    pickle_file = open(
                        os.path.join(self.zonedir, "pickled_metadata"), "w", encoding="utf-8"
                    )
                    pickle_file.write(pickled_metadata)
                    pickle_file.close()
                    # Save the zone data dictionary for easy reading
                    pickle_file = open(
                        os.path.join(self.zonedir, "zone_dictionary"), "w", encoding="utf-8"
                    )
                    pickle_file.write(pprint.pformat(zones))
                    pickle_file.close()

    def get_metadata(self, zones):
        """Concatenates glue and a records together to make a single zone file

        Once a single file for each zone is generated, pickle and encode them
        so they can be distributed by the metadata server.

        Arguments:
            zones (dict): All generated zone files for the topology

        Returns:
            str: The pickled zone metadata.
        """
        metadata = {}
        for zone in zones:
            zone_file_contents = f"{self.get_boilerplate(zone)}"
            if "glue" in zones[zone]:
                zone_file_contents += f"\n{zones[zone]['glue']}"
            if "%RR%" in zones[zone]:
                zone_file_contents += f"\n{zones[zone]['%RR%']}"
            metadata[zone] = zone_file_contents

            if self.DEBUG:
                if not zone:
                    zone = "dot."
                zone_file = open(os.path.join(self.zonedir, zone), "w", encoding="utf-8")
                zone_file.write(zone_file_contents)
                zone_file.close()

        pickled_metadata = pickle.dumps(metadata, protocol=0).decode()
        return pickled_metadata

    def generate_zone_files(self, zones, dns_server):
        """Function to seed the recursion of the dictionary.

        Arguments:
            zones(dict): Dictionary containing information on all
                zones in the topology.
            dns_server(str): The IP address of the dns server in the topology
        """
        self.walk_zones(zones, "", dns_server)
        self.generate_root_glue_record(zones, dns_server)

    def walk_zones(self, zones, domain, dns_server):
        """Walks the dictionary creating a records and glue records

        Arguments:
            zones(dict): Dictionary containing information on all zones in the
                topology.
            domain(str): The base for the current machine's fully qualified
                domain name
            dns_server(str): The IP address of the dns server in the topology
        """

        for zone in zones:
            base_domain = f"{zone}.{domain}"
            if isinstance(zones[zone], dict):
                self.generate_glue_record(zone, base_domain, dns_server)
                self.walk_zones(zones[zone], base_domain, dns_server)

        self.generate_records(zones, domain)

    def generate_glue_record(self, zone_name, base_domain, dns_server):
        """Creates a glue record for the current zone

        Looks for all branches stemming from this point in the tree.
        Skips any definitions of singular machines.

        Arguments:
            zone_name(str): Current zone in the dictionary
            base_domain(str): Base name for the fully qualified domain name
            dns_server(str): The IP address of the dns_server
        """
        glue_record = ""
        zone_name += "."
        fqdn = f"ns.{base_domain}"
        glue_record += f"{base_domain}\tIN\tNS\t{fqdn}\n"
        glue_record += f"{fqdn}\tIN\tA\t{dns_server}\n\n"

        if glue_record:
            if base_domain not in self.bind_zones:
                self.bind_zones[base_domain] = {}
            self.bind_zones[base_domain]["glue"] = glue_record

        if self.DEBUG:
            if glue_record:
                gr_file = open(
                    os.path.join(self.zonedir, f"{base_domain}{'glue'}"), "w", encoding="utf-8"
                )
                gr_file.write(glue_record)
                gr_file.close()

    def generate_root_glue_record(self, root_zone, dns_server):
        """
        Creates a glue record for the root zone.

        Arguments:
            root_zone(dict): The root zone for which to create a glue record
            dns_server(str): IP address of the dns_server in the topology
        """
        base_domain = ""
        glue_record = ""

        glue_record += ". IN NS ns.\n"
        glue_record += f"ns. IN A {dns_server}\n"

        for zone in root_zone:
            if isinstance(root_zone[zone], dict):
                fqdn = f"ns.{zone}."
                glue_record += f"{zone}.\tIN\tNS\t{fqdn}\n"
                glue_record += f"{fqdn}\tIN\tA\t{dns_server}\n\n"

        if glue_record:
            if base_domain not in self.bind_zones:
                self.bind_zones[base_domain] = {}
            self.bind_zones[base_domain]["glue"] = glue_record

        if self.DEBUG:
            if glue_record:
                gr_file = open(os.path.join(self.zonedir, f"{'dot.'}{'glue'}"), "w", encoding="utf-8")
                gr_file.write(glue_record)
                gr_file.close()

    def generate_records(self, zones, base_domain):
        """Creates the records for a single machine in the topology

        Arguments:
            zones (dict): Current subtree of the total zones dictionary
            base_domain (str): The base name for the fully qualified domain name
        """
        found_node = False
        record = ""
        for zone in zones:
            if not isinstance(zones[zone], list):
                continue
            found_node = True
            for entry in zones[zone]:
                if len(entry) == 3:
                    # We have a special subdomain to add to the zone
                    (subdomain, resource_type, resource_record) = entry
                else:
                    # The subdomain to add to the zone is the zone origin
                    (resource_type, resource_record) = entry
                    subdomain = zone
                record += f"{subdomain}\tIN\t{resource_type}\t{resource_record}\n"

        if not found_node:
            return

        # Save the record for later, when it will be concatenated with other
        # records
        if record:
            if base_domain not in self.bind_zones:
                self.bind_zones[base_domain] = {}
            self.bind_zones[base_domain]["%RR%"] = record

        if self.DEBUG:
            if not base_domain:
                base_domain = "dot."
            ar_file = open(os.path.join(self.zonedir, f"{base_domain}{'a'}"), "w", encoding="utf-8")
            ar_file.write(record)
            ar_file.close()

    def get_boilerplate(self, zone):
        """Creates a boiler plate for the combined record files.

        Arguments:
            zone(str): The fully qualified domain name for this zone

        Returns:
            str: The boiler plate string that is created.
        """
        bp_str = ""
        if not zone:
            bp_str += "$ORIGIN .\n"
        else:
            bp_str += f"$ORIGIN {zone}\n"
        bp_str += "$TTL 5m\n"
        bp_str += f"@ IN SOA ns.{zone} noemail.noreply.org (\n"
        bp_str += f"\t\t\t{CONFIG['boilerplate_serial']}\n"
        bp_str += f"\t\t\t{CONFIG['boilerplate_refresh']}\n"
        bp_str += f"\t\t\t{CONFIG['boilerplate_retry']}\n"
        bp_str += f"\t\t\t{CONFIG['boilerplate_expire']}\n"
        bp_str += f"\t\t\t{CONFIG['boilerplate_minimum']} )\n"

        return bp_str
