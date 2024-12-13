.. _dns.dns_objects_mc:

###############
dns.dns_objects
###############

This model component provides the :py:class:`dns.dns_objects.DNSServer` object, which can be added to the Experiment Graph.

**Model Component Dependencies:**
    * :ref:`linux.ubuntu1604_mc`


************
VM Resources
************

.. warning::
    This MC utilizes an older version of Ubuntu and Bind as the DNS server. It may need updates or modifications to work with newer experiments.

* ``bind9_xenial_debs.tgz`` - The `BIND 9 <https://www.isc.org/bind/>`_ software packages for Ubuntu 16.04 (Xenial) as downloaded from `launchpad <https://launchpad.net/ubuntu/+source/bind9/1:9.10.3.dfsg.P4-8ubuntu1.15/+build/17413822>`_.

*****************
Available Objects
*****************

.. automodule:: dns.dns_objects
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__
