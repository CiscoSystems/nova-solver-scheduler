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

from nova.scheduler.filters import affinity_filter
from nova.scheduler.solvers import constraints


class SameHostConstraint(constraints.BaseLinearConstraint):
    """Schedule the instance on the same host as another instance in a set
    of instances.
    """

    def _generate_components(self, variables, hosts, filter_properties):
        num_hosts = len(hosts)
        num_instances = filter_properties.get('num_instances')

        var_matrix = variables.host_instance_matrix

        for i in xrange(num_hosts):
            host_passes = affinity_filter.SameHostFilter().host_passes(
                                                hosts[i], filter_properties)
            if not host_passes:
                for j in xrange(num_instances):
                    self.variables.append([var_matrix[i][j]])
                    self.coefficients.append([1])
                    self.constants.append(0)
                    self.operators.append('==')


class DifferentHostConstraint(constraints.BaseLinearConstraint):
    """Schedule the instance on a different host from a set of instances."""

    def _generate_components(self, variables, hosts, filter_properties):
        num_hosts = len(hosts)
        num_instances = filter_properties.get('num_instances')

        var_matrix = variables.host_instance_matrix

        for i in xrange(num_hosts):
            host_passes = affinity_filter.DifferentHostFilter().host_passes(
                                                hosts[i], filter_properties)
            if not host_passes:
                for j in xrange(num_instances):
                    self.variables.append([var_matrix[i][j]])
                    self.coefficients.append([1])
                    self.constants.append(0)
                    self.operators.append('==')