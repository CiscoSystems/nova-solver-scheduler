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


class NonTrivialSolutionConstraint(linearconstraints.BaseLinearConstraint):
    """Constraint that forces each instance to be placed
    at exactly one host, so as to avoid trivial solutions.
    """

    def _generate_components(self, variables, hosts, filter_properties):
        num_hosts = len(hosts)
        num_instances = filter_properties.get('num_instances')

        var_matrix = variables.host_instacne_adjacency_matrix

        for j in xrange(num_instances):
            self.variables.append(
                    [var_matrix[i][j] for i in range(num_hosts)])
            self.coefficients.append([1 for i in range(num_hosts)])
            self.constants.append(1)
            self.operators.append('==')
