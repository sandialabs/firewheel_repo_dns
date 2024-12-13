from base_objects import Switch
from dns.dns_objects import DNSServer

from firewheel.control.experiment_graph import AbstractPlugin


class PopulateZones(AbstractPlugin):
    """This plugin builds the zone graphs needed for DNS.
    The plugin first walks the entire graph, building a graph of
    the zone data for the system, and installs that on
    the master dns server (usually named DNS).
    It then walks the graph to find each in-experiment node marked
    as a dns server and uses a similar process to add zone data for it.
    In each case, it puts the zone graphs on each dns server node
    of the Firewheel graph.
    """

    def run(self):
        """Function to invoke the ConfigureDNS plugin."""

        # Create zones for in-experiment dns servers
        for vertex in self.g.get_vertices():
            # Look for dns key {'dns':{"server" "dns.ssn.gov",
            #                          "hosts_tracked": ...}}
            if vertex.is_decorated_by(DNSServer):
                name = vertex.name
                hosts_tracked = vertex.dns_data.get("hosts_tracked")
                if not hosts_tracked:
                    hosts_tracked = "*"
                zones = self.populate_zones(name, hosts_tracked)
                self.log.debug("Zones for %s:", name)
                self.log.debug(zones)
                vertex.dns_data["zones"] = zones

    def populate_zones(self, dns_server_name, hosts_tracked):
        """
        Walk the graph building a dictionary which specifies the zones in the graph.

        The many level dictionary allows the generation function to easily
        figure out the contents of potential A records and glue records.

        Arguments:
            dns_server_name (str): The name of the DNS server
            hosts_tracked (list): The hosts that the DNS server is tracking

        Returns:
            dict: The DNS zone dictionary.
        """

        zones = {}
        self.log.debug(
            "PTRs requested for %s = %s", dns_server_name, str(hosts_tracked)
        )

        vertices = self.g.get_vertices()
        for vertex in vertices:
            if vertex.get("deleted"):
                continue
            if not vertex.is_decorated_by(Switch):
                full_name = vertex.name
                name = full_name.split(".")
                name.reverse()
                try:
                    interfaces = vertex.interfaces.interfaces
                except AttributeError:
                    self.log.warning(
                        "Vertex with name=%s did not have an interface, ignoring",
                        vertex.name,
                    )
                    continue
                address = None

                # pull address
                if not interfaces:
                    continue

                if vertex.is_decorated_by(DNSServer):
                    # continue
                    pass

                for iface in interfaces:
                    if "switch" in iface:
                        address = iface["address"]
                        break

                if not address:
                    # This VM is not part of the experiment, but that's okay
                    continue

                # Skip any machines this server doesn't care about.
                if hosts_tracked == "*" or full_name in hosts_tracked:
                    pass
                else:
                    continue

                # populate the dictionary
                current_location = zones
                for name_index, component in enumerate(name):
                    if component not in current_location:
                        if name_index == (len(name) - 1):
                            current_location[component] = [("A", address)]
                        else:
                            current_location[component] = {}
                        current_location = current_location[component]
                    else:
                        current_location = current_location[component]

                # Create the PTR record
                ptr_addr = f"arpa.in-addr.{address}"
                ptr_addr = ptr_addr.split(".")

                current_location = zones
                for ptr_addr_index, component in enumerate(ptr_addr):
                    if component not in current_location:
                        if ptr_addr_index == (len(ptr_addr) - 1):
                            current_location[component] = [("PTR", f"{full_name}.")]
                        else:
                            current_location[component] = {}
                        current_location = current_location[component]
                    else:
                        current_location = current_location[component]

        return zones
