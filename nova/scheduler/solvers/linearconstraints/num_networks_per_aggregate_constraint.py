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

LOG = logging.getLogger(__name__)


class NumNetworksPerAggregateConstraint(
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
        remain_networks = [0 for i in range(self.num_hosts)]
        for i in range(self.num_hosts):
            aggregate_stats = hosts[i].host_aggregates_stats
            min_remain_aggregate_networks = 0
            for aggregate in aggregate_stats.values():
                aggregate_metadata = aggregate.get('metadata', {})
                max_networks_allowed = aggregate_metadata.get('max_networks', None)
                aggregate_networks = aggregate.get('networks', None)
                if max_networks is None or aggregate_networks is None:
                        continue
                num_aggregate_networks = len(aggregate_networks)
                remain_aggregate_networks = max_networks_allowed - num_aggregate_networks
                for network_id, requested_ip, port_id in requested_networks:
                    if network_id:
                        if network_id not in aggregate_networks:
                            remain_aggregate_networks -= 1
                if remain_aggregate_networks < min_remain_aggregate_networks:
                    min_remain_aggregate_networks = remain_aggregate_networks
            remain_networks[i] = min_remain_aggregate_networks

        for i in range(self.num_hosts)]:
            coefficient_vectors = [
                    [-remain_networks[i]
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
    