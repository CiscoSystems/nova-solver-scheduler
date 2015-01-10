# Copyright (c) 2011-2012 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging
from nova.scheduler.solvers import linearconstraints


class PciPassthroughConstraint(linearconstraints.BaseLinearConstraint):
    """Constraint that schedules instances on a host if the host has devices
    to meet the device requests in the 'extra_specs' for the flavor.

    PCI resource tracker provides updated summary information about the
    PCI devices for each host, like:
    [{"count": 5, "vendor_id": "8086", "product_id": "1520",
        "extra_info":'{}'}],
    and VM requests PCI devices via PCI requests, like:
    [{"count": 1, "vendor_id": "8086", "product_id": "1520",}].

    The constraint checks if the host passes or not based on this information.
    """

    def get_coefficient_vectors(self, variables, hosts, instance_uuids,
                                request_spec, filter_properties):
        coefficient_vectors = []
        pci_requests = filter_properties.get('pci_requests')
        if not pci_requests:
            coefficient_vectors = [[0 for j in range(self.num_instances)]
                                    for i in range(self.num_hosts)]
            return coefficient_vectors
        for host in hosts:
            if host.pci_stats.support_requests(pci_requests):
                coefficient_vectors.append([0
                        for j in range(self.num_instances)])
            else:
                coefficient_vectors.append([1
                        for j in range(self.num_instances)])

        return coefficient_vectors

    def get_variable_vectors(self, variables, hosts, instance_uuids,
                            request_spec, filter_properties):
        variable_vectors = []
        variable_vectors = [[variables[i][j] for j in range(
                    self.num_instances)] for i in range(self.num_hosts)]
        return variable_vectors

    def get_operations(self, variables, hosts, instance_uuids, request_spec,
                        filter_properties):
        operations = [(lambda x: x == 0) for i in range(self.num_hosts)]
        return operations
