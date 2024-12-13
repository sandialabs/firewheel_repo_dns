#!/usr/bin/env python
import sys
import pickle
from subprocess import call


# pylint: disable=useless-object-inheritance
class ConfigureDNS(object):
    """
    This VM Resource helps to configure DNS using ``bind``.
    """

    name = "configure_dns"
    sleep_time = 30

    def __init__(self, ascii_file=None, binary_file=None):
        """
        Initialize the configuration file as a class variable.

        Arguments:
            ascii_file (str): The path to the configuration file, which should contain
                a dictionary in pickle format. The dictionary should contain information
                about the DNS zones.
            binary_file (str): This is not used, but kept for backwards compatibility.
        """
        self.ascii_file = ascii_file

    def run(self):
        """
        The primary method for setting up bind.
        This method reads in the configuration, and places it in the bind configuration
        file. Then, the ``bind9`` service is restarted.
        """
        # Get the binary files to install BIND
        with open(self.ascii_file, "r") as ascii_data:
            zone_files = ascii_data.read()

        # unpickle the dictionary
        zone_files = pickle.loads(zone_files)

        # Do not include default zones in bind's config
        with open("/etc/bind/named.conf", "w") as named_conf:
            named_conf.write('include "/etc/bind/named.conf.options";\n')
            named_conf.write('include "/etc/bind/named.conf.local";\n')

        with open("/etc/bind/named.conf.local", "w") as local_conf:

            for zone in zone_files:
                # place this zone file in the right location
                if not zone:
                    zone_file_location = "/var/lib/bind/db.root"
                else:
                    zone_file_location = "/var/lib/bind/db.%s" % zone
                with open(zone_file_location, "w") as zone_file:
                    zone_file.write(zone_files[zone])

                # add this zone as a block in
                # named.conf.local
                if not zone:
                    conf = 'zone "."{\n\ttype master;\n\tfile "%s";\n};\n' % (
                        zone_file_location
                    )
                else:
                    conf = 'zone "%s"{\n\ttype master;\n\tfile "%s";\n};\n' % (
                        zone,
                        zone_file_location,
                    )
                local_conf.write(conf)

        # There is no passed in data, so this is safe
        call("service bind9 restart", shell=True)  # noqa: DUO116


if __name__ == "__main__":
    configure = ConfigureDNS(sys.argv[1])
    configure.run()
