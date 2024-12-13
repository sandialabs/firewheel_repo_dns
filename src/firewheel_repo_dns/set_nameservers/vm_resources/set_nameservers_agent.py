#!/usr/bin/env python3

import os
import sys
import json
from abc import ABCMeta, abstractmethod
from platform import system
from subprocess import call


class SetNameservers:
    """
    This is an abstract class which is used to host common functionality between setting
    name servers on Linux vs Windows.
    """

    # This is still run on Python2 VMs, therefore we should ignore linting errors
    __metaclass__ = ABCMeta  # noqa: B303

    def run(self, args):
        """
        This sets up the creation of a list with all the name servers.

        Arguments:
            args (list): The arguments passed into the VMR. The first argument
                should be a path to a file containing line separated list of the
                name servers.
        """
        ascii_file = args[1]

        self.nameservers = []
        with open(ascii_file, "r") as fhand:
            for server in fhand:
                self.nameservers.append(server.strip())

        self.set_nameservers()

    @abstractmethod
    def set_nameservers(self):
        """
        Abstract method, that should be overridden.
        """


class SetNameserversLinuxResolvConf(SetNameservers):
    """
    This class sets the name servers for Linux based computers by either
    updating ``resolveconf`` or setting it in the netplan configuration.
    """

    def set_nameservers(self):
        """
        Set's the name servers and restarts the service.
        """
        # Check if netplan is installed
        try:
            netplan_enabled = call(["netplan", "info"]) == 0
        except OSError:
            netplan_enabled = False
        if netplan_enabled:
            with open("/etc/netplan/firewheel.yaml") as f_hand:
                fw_netplan = json.load(f_hand)
            ethernets = fw_netplan["network"]["ethernets"]
            for interface in ethernets.keys():
                ethernets[interface]["nameservers"] = {"addresses": self.nameservers}
            with open("/etc/netplan/firewheel.yaml", "w") as f_hand:
                json.dump(fw_netplan, f_hand, indent=4)
            if call(["netplan", "apply"]) != 0:
                print("ERROR applying firewheel netplan configuration")
        else:
            base_path = "/etc/resolvconf/resolv.conf.d"
            if not os.path.exists(base_path):
                os.makedirs(base_path)
            with open(os.path.join(base_path, "head"), "a") as resolv_conf:
                for address in self.nameservers:
                    server = "nameserver %s\n" % address
                    resolv_conf.write(server)
            if call(["/usr/sbin/service", "resolvconf", "restart"]) != 0:
                print("ERROR: unable to restart resolvconf")
                os.remove(os.path.join(base_path, "head"))


class SetNameserversWindows(SetNameservers):
    """
    This class sets the name servers for Windows based computers.
    """

    def set_nameservers(self):
        """
        Set's the name servers.
        """
        address_list_str = ""
        count_addrs = 0
        for address in self.nameservers:
            if count_addrs == 0:
                address_list_str = '"%s"' % address
            else:
                address_list_str.append(', "%s"' % address)
            count_addrs = count_addrs + 1

        objs = "(Get-WmiObject Win32_NetworkAdapterConfiguration -Filter \"ipenabled = 'true'\")"
        meth = "SetDNSServerSearchOrder(%s)" % address_list_str
        cmd = "foreach($NIC in %s) {$NIC.%s}" % (objs, meth)
        if call(["powershell", cmd]) != 0:
            print("ERROR: could not set dnsserver")


if __name__ == "__main__":
    operating_system = system()
    if operating_system == "Linux":
        sns = SetNameserversLinuxResolvConf()
    elif operating_system == "Windows":
        sns = SetNameserversWindows()

    sns.run(sys.argv)
