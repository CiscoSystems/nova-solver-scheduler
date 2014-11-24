# Copyright (c) 2014 Cisco Systems Inc.
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

from oslo.config import cfg

from nova.openstack.common import log as logging
from nova.scheduler.solvers import linearconstraints

CONF = cfg.CONF
CONF.import_opt("max_networks_per_rack", "nova.scheduler.filters.num_networks_per_host_rack_filter")

LOG = logging.getLogger(__name__)


class NumNetworksPerRackConstraint(
        linearconstraints.BaseLinearConstraint):
    """Constraint that specifies the maximum number of networks that
    each rack can launch.
    """

    # The linear constraint should be formed as:
    # coeff_matrix * var_matrix' (operator) (constants)
    # where (operator) is ==, >, >=, <, <=, !=, etc.
    # For convenience, the (constants) is merged into left-hand-side,
    # thus the right-hand-side is 0.

    def __init__(self, variables, hosts, instance_uuids, request_spec,
                filter_properties):
        [self.num_hosts, self.num_instances] = self._get_host_instance_nums(
                                        hosts, instance_uuids, request_spec)

    def _get_host_instance_nums(self, hosts, instance_uuids, request_spec):
        """This method calculates number of hosts and instances."""
        num_hosts = len(hosts)
        if instance_uuids:
            num_instances = len(instance_uuids)
        else:
            num_instances = request_spec.get('num_instances', 1)
        return [num_hosts, num_instances]

    def get_coefficient_vectors(self, variables, hosts, instance_uuids,
                                request_spec, filter_properties):
        """Calculate the coeffivient vectors."""
        # The coefficient for each variable is 1 and constant in
        # each constraint is -(max_instances_per_host)
        requested_networks = filter_properties.get('requested_networks', None)
        max_networks_allowed = CONF.max_networks_per_rack
        num_networks_after = [0 for i in range(self.num_hosts)]
        for i in range(self.num_hosts):
            rack_networks_list = hosts[i].aggregated_networks.values()
            max_num_rack_networks_after = max([len(rack_networks) for rack_networks in rack_networks_list])
            for rack_networks in rack_networks_list:
                num_rack_networks_before = len(rack_networks)
                num_rack_networks_after = num_rack_networks_before
                for network_id, requested_ip, port_id in requested_networks:
                    if network_id:
                        if network_id not in rack_networks:
                            num_rack_networks_after += 1
                if num_rack_networks_after > max_num_rack_networks_after:
                    max_num_rack_networks_after = num_rack_networks_after
            num_networks_after[i] = max_num_rack_networks_after

        for i in range(self.num_hosts)]:
            coefficient_vectors = [
                    [num_networks_after[i] - max_networks_allowed
                    for j in range(self.num_instances)]
                    for i in range(self.num_hosts)]
        return coefficient_vectors

    def get_variable_vectors(self, variables, hosts, instance_uuids,
                            request_spec, filter_properties):
        """Reorganize the variables."""
        # The variable_matrix[i,j] denotes the relationship between
        # host[i] and instance[j].
        variable_vectors = []
        variable_vectors = [[variables[i][j] for j in range(
                    self.num_instances)] for i in range(self.num_hosts)]
        return variable_vectors

    def get_operations(self, variables, hosts, instance_uuids, request_spec,
                        filter_properties):
        """Set operations for each constraint function."""
        # Operations are '<='.
        operations = [(lambda x: x <= 0) for i in range(self.num_hosts)]
        return operations
    