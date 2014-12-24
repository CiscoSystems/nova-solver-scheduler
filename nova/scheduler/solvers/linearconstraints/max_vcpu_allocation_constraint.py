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

from nova.scheduler.solvers import linearconstraints

CONF = cfg.CONF
CONF.import_opt('cpu_allocation_ratio', 'nova.scheduler.filters.core_filter')


class MaxVcpuAllocationPerHostConstraint(
        linearconstraints.BaseLinearConstraint):
    """Constraint of the total vcpu demand acceptable on each host."""

    # The linear constraint should be formed as:
    # coeff_vectors * var_vectors' (operator) (constants)
    # where (operator) is ==, >, >=, <, <=, !=, etc.
    # For convenience, the (constants) is merged into left-hand-side,
    # thus the right-hand-side is 0.

    def get_coefficient_vectors(self, variables, hosts, instance_uuids,
                                request_spec, filter_properties):
        # Give demand as coefficient for each variable and -supply as constant
        # in each constraint.
        demand = [self._get_required_vcpus(filter_properties)
                  for j in range(self.num_instances)]
        supply = [self._get_usable_vcpus(hosts[i])
                  for i in range(self.num_hosts)]
        coefficient_vectors = [demand + [-supply[i]]
                              for i in range(self.num_hosts)]
        return coefficient_vectors

    def get_variable_vectors(self, variables, hosts, instance_uuids,
                             request_spec, filter_properties):
        # The variable_vectors[i,j] denotes the relationship between host[i]
        # and instance[j].
        variable_vectors = []
        variable_vectors = [[variables[i][j]
                             for j in range(self.num_instances)]
                            + [1] for i in range(self.num_hosts)]
        return variable_vectors

    def get_operations(self, variables, hosts, instance_uuids, request_spec,
                       filter_properties):
        # Operations are '<='.
        operations = [(lambda x: x <= 0) for i in range(self.num_hosts)]
        return operations

    def _get_usable_vcpus(self, host_state):
        """This method returns the usable vcpus for the given host.
        """
        vcpus_total = host_state.vcpus_total * CONF.cpu_allocation_ratio
        usable_vcpus = vcpus_total - host_state.vcpus_used
        return usable_vcpus

    def _get_required_vcpus(self, filter_properties):
        """This method returns the required vcpus from
           the given filter_properties dictionary object.
        """
        required_vcpus = 1
        instance_type = filter_properties.get('instance_type')
        if instance_type is not None:
            required_vcpus = instance_type.get('vcpus', 1)
        return required_vcpus
