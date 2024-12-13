from base_objects import Switch, VMEndpoint
from dns.dns_objects import DNSServer
from linux.base_objects import LinuxHost

from firewheel.control.experiment_graph import AbstractPlugin


class SetNameservers(AbstractPlugin):
    """This plugin sets the DNS nameservers for each host in the
    experiment graph.
    """

    def __init__(self, *args, **kwargs):
        """Constructor for ConfigureDNS

        Arguments:
            *args: extra args to pass to AbstractPlugin constructor
            **kwargs: extra keyword args to pass to AbstractPlugin constructor
        """
        super(SetNameservers, self).__init__(*args, **kwargs)

    def run(self):
        """
        Set the nameservers of each VM in the experiment.
        """
        dns_ips = []
        for v in self.g.get_vertices():
            if v.is_decorated_by(DNSServer):
                dns_ips.append(str(v.dns_data.get("dns_address")))
        for v in self.g.get_vertices():
            if v.is_decorated_by(Switch):
                # Set the dns1 option in each switch
                dns = dns_ips
                v["dns1"] = ""
                if 0:
                    v["dns1"] = dns[0]
                v["dns2"] = ""

            if v.is_decorated_by(VMEndpoint):
                # Add it to the host's schedule
                # See if the node has application data to override
                # the default name server
                ns_conf = None
                if v.is_decorated_by(DNSServer):
                    ns_conf = v.dns_data.get("nameserver_address")
                if ns_conf:
                    ns_conf = str(ns_conf)
                else:
                    ns_conf = "\n".join(dns_ips)
                    self.log.debug(
                        "set nameservers from dns_ips for %s to %s",
                        v.name,
                        ",".join(dns_ips),
                    )
                    v.dns_nameservers = ns_conf
                # Only run the set_nameservers_agent.py python script on
                # LinuxHosts since Windows images do not have python installed
                # by default. Windows does per interface DNS server settings and
                # will pick up the servers from self.dns_nameservers in configure_ips
                if v.is_decorated_by(LinuxHost):
                    v.add_vm_resource(-99, "set_nameservers_agent.py", ns_conf, None)
