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

from nova.scheduler.solvers import constraints


class ValidSolutionConstraint(constraints.BaseLinearConstraint):
    """The constraint must be configured when using spread/stack featured
    costs, e.g. RAM cost. It ensures that all '1's appear in front of any '0'
    in each row of the host-instance matrix solution.
    """

    def _generate_components(self, variables, hosts, filter_properties):
        num_hosts = len(hosts)
        num_instances = filter_properties.get('num_instances')

        var_matrix = variables.host_instance_matrix

        if num_instances <= 1:
            return

        for i in xrange(num_hosts):
            for j in xrange(num_instances - 1):
                self.variables.append(
                        [var_matrix[i][j], var_matrix[i][j + 1]])
                self.coefficients.append([1, -1])
                self.constants.append(0)
                self.operators.append('>=')
