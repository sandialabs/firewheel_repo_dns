from linux.ubuntu1604 import Ubuntu1604Server

from firewheel.control.experiment_graph import require_class


@require_class(Ubuntu1604Server)
class DNSServer:
    """This graph_object provides DNS services for all nodes in
    in the experiment graph.
    """

    def __init__(self, dns_ip):
        """
        Create the ``dns_data`` dictionary attribute which initializes
        many DNS parameters.

        Arguments:
            dns_ip (str): The IP Address of the DNS server.
        """
        self.dns_data = {}
        self.dns_data["server"] = True
        self.dns_data["hosts_tracked"] = "*"
        self.dns_data["dns_address"] = dns_ip
        self.install_bind()

    def install_bind(self, start_time=-20):
        """Installs the bind9 debian packages.

        Arguments:
            start_time (int): The time at which to install bind. Defaults to -20.
        """
        self.install_debs(start_time, "bind9_xenial_debs.tgz")
