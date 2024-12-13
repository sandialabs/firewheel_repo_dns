.. _dns.insert_dns:

##################
dns.insert_dns
##################

Overview:
The insert_dns model component provides an easy way to drop a configured DNS server onto an arbitrary experiment graph.

It consists of the following components:
(1) dns.dns_objects, which provides the DNSServer graph_object. The DNSServer is a Ubuntu 16.04 server running bind.

(2) A series of model_components that configure the DNSServer as well as the rest of the hosts in the experiment graph:
populate_zones, builds the dns zone graphs for the experiment graph
insert_records,  inserts additional records into the DNSServer
configure_bind, configures bind for each DNSServer
set_nameservers, sets the dns nameserver for each host

Requirements:
Generally the requirements in order to use a configured DNSServer in an experiment graph are:
(1) The DNS model components must be downloaded onto the host and made accessible to firewheel through firewheel repository install.
(2) The model_component in which you plan to use a DNSServer graph_object depends on the dns.dns_objects model_component.
(3) The "dns" attribute is depended on before minimega.launch and after topology.

Example -- Adding DNS to the ACME Topology Plugin
-------------------------------------------------

Getting Started
^^^^^^^^^^^^^^^

If you haven't already cloned and installed the linux model_component repository into firewheel, do the following:


(1) clone the linux model_component repository to /opt/firewheel/linux

(2) run firewheel repository install /opt/firewheel/linux.

Likewise, because we are modifying the acme experiment, ensure you have the acme model_component repository installed.

Overview
^^^^^^^^
The acme experiment contains the following model_components: topology, set_hostname, and run.
We will be making modifications to acme.topology and acme.run.


acme.run depends on the other model_components, so the entire experiment can be launched from the command line with::

$ firewheel experiment acme.run minimega.launch

Adding Required Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
We want to add a DNSServer object to the acme.topology model_component.
We also want the DNSServer to be configured when we run acme.run.

1. Add "dns.dns_objects" model_component dependencies of the acme.topology MANIFEST file.


2. Import the DNSServer object to our acme.topology plugin by adding::

    from dns.dns_objects import DNSServer

  to the top of the plugin.

3. Add the "dns" attribute to the attribute dependencies of acme.run MANIFEST file.


Adding DNSServer to Our Plugin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Let's instantiate the DNSServer in our plugin and add it to the experiment graph.

In our case, we can add the DNSServer to building_1 by modifying the build_building1 function.
At the end of the function, we can add::

  dns_server = Vertex(self.g, "dns.acme.com")
  dns_server.decorate(DNSServer, init_args=[b1_network[5]])
  dns_server.connect(b1_int, b1_network[5], b1_network.netmask)

Launching the New Experiment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Our experiment should run with::

$ firewheel experiment acme.topology minimega.launch

Now let's  verify whether our DNSServer was correctly added and configured.

First let's verify that the dns.acme.com VM was added::

$ firewheel vm list vnc state image

An excerpt of the expected output of the above command is shown below. You should see, among other items, dns.acme.com: ::

    +----------------------+-------+---------------------+------------------------------------+
    | dns.acme.com         | 5906  | running/configuring | ubuntu-16.04.3-server-amd64.qc2.xz |
    +----------------------+-------+---------------------+------------------------------------+
    | b2-0.acme.com        | 5908  | running/configuring | ubuntu-16.04.3-server-amd64.qc2.xz |
    +----------------------+-------+---------------------+------------------------------------+

Once all of the VMs have the status running/configured, VNC into one of the Ubuntu desktops.
In our case we will VNC into 5908 which belongs to b2-0.acme.com as shown above.

Log into the VM with the default credentials of ubuntu:ubuntu.


Verify whether nslookup works for the DNS server ::

  $ nslookup dns.acme.com

  Server:       10.30.10.5
  Address:      10.30.10.5#53

  Name:         10.30.10.5
  Address:      10.30.10.5

Verify whether nslookup works for the the ``datacenter`` ::

  $ nslookup datacenter.acme.com

  Server:       10.30.10.5
  Address:      10.30.10.5#53

  Name:         datacenter.acme.com
  Address:      10.30.3.2

**Attribute Provides:**
    * ``dns``

**Attribute Depends:**
    * ``topology``

**Model Component Dependencies:**
    * :ref:`dns.populate_zones_mc`
    * :ref:`dns.insert_records_mc`
    * :ref:`dns.configure_bind_mc`
    * :ref:`dns.set_nameservers_mc`
