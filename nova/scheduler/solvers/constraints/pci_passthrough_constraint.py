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

import copy

from nova.scheduler.solvers import constraints


class PciPassthroughConstraint(constraints.BaseLinearConstraint):
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

    def _get_acceptable_pci_requests_times(self, max_times_to_try,
                                                pci_requests, host_pci_stats):
        acceptable_times = 0
        while acceptable_times < max_times_to_try:
            if host_pci_stats.support_requests(pci_requests):
                acceptable_times += 1
                host_pci_stats.apply_requests(pci_requests)
            else:
                break
        return acceptable_times

    def _generate_components(self, variables, hosts, filter_properties):
        num_hosts = len(hosts)
        num_instances = filter_properties.get('num_instances')

        var_matrix = variables.host_instance_matrix

        pci_requests = filter_properties.get('pci_requests'):
        if not pci_requests:
            return

        for i in xrange(num_hosts):
            host_pci_stats = copy.deepcopy(hosts[i].pci_stats)
            acceptable_pci_requests_times = (
                    self._get_acceptable_pci_requests_times(num_instances,
                                                pci_requests, host_pci_stats))

            self.variables.append(
                    [var_matrix[i][j] for j in range(num_instances)])
            self.coefficients.append(
                    [1 for j in range(num_instances)])
            self.constants.append(acceptable_pci_requests_times)
            self.operators.append('<=')
