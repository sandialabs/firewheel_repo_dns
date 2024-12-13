from dns.dns_objects import DNSServer

from firewheel.control.experiment_graph import AbstractPlugin


class InsertRecords(AbstractPlugin):
    """Plugin to insert extra records into the zones data"""

    def __init__(self, *args, **kwargs):
        """Constructor for ConfigureDNS

        Arguments:
            *args: extra args to pass to AbstractPlugin constructor
            **kwargs: extra keyword args to pass to AbstractPlugin constructor
        """
        super(InsertRecords, self).__init__(*args, **kwargs)

    def run(self):
        """Function to run the InsertDNS plugin"""

        for vertex in self.g.get_vertices():
            # Look for zones and special records on dns key
            if vertex.is_decorated_by(DNSServer):
                self.add_records(vertex)

    def add_records(self, vertex):
        """Add dns records to the zone data.

        Arguments:
            vertex(firewheel.control.experiment_graph.Vertex): The graph vertex to add the records to
        """
        addon_records = vertex.dns_data.get("addon_records")
        zones = vertex.dns_data.get("zones")
        if zones and addon_records:
            # this means that we have some records to add to the zone data

            # Merge special records at top-level-domain level.
            for tld in addon_records:
                if zones.get(tld):
                    zones[tld].update(addon_records[tld])
                else:
                    zones[tld] = addon_records[tld]
            vertex.dns_data["zones"] = zones
