# Copyright (c) 2014 Cisco Systems, Inc.
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
from nova.scheduler.solvers import constraints

LOG = logging.getLogger(__name__)


class ServerGroupAffinityConstraint(constraints.BaseLinearConstraint):
    """Force to select hosts which host given server group."""

    def __init__(self, *args, **kwargs):
        super(ServerGroupAffinityConstraint, self).__init__(*args, **kwargs)
        self.policy_name = 'affinity'

    def _generate_components(self, variables, hosts, filter_properties):
        num_hosts = len(hosts)
        num_instances = filter_properties.get('num_instances')

        var_matrix = variables.host_instacne_adjacency_matrix

        policies = filter_properties.get('group_policies', [])
        if self.policy_name not in policies:
            return

        group_hosts = filter_properties.get('group_hosts')

        if not group_hosts:
            for i in xrange(num_hosts):
                self.variables.append(
                            [var_matrix[i][j] for j in range(num_instances)])
                self.coefficients.append([1 - num_instances] +
                                        [1 for j in range(num_instances - 1)])
                self.constants.append(0)
                self.operators.append('==')
        else:
            for i in xrange(num_hosts):
                if hosts[i].host not in group_hosts:
                    for j in xrange(num_instances):
                        self.variables.append([var_matrix[i][j]])
                        self.coefficients.append([1])
                        self.constants.append(0)
                        self.operators.append('==')


class ServerGroupAntiAffinityConstraint(constraints.BaseLinearConstraint):
    """Force to select hosts which host given server group."""

    def __init__(self, *args, **kwargs):
        super(ServerGroupAntiAffinityConstraint, self).__init__(
                                                            *args, **kwargs)
        self.policy_name = 'anti-affinity'

    def _generate_components(self, variables, hosts, filter_properties):
        num_hosts = len(hosts)
        num_instances = filter_properties.get('num_instances')

        var_matrix = variables.host_instacne_adjacency_matrix

        policies = filter_properties.get('group_policies', [])
        if self.policy_name not in policies:
            return

        group_hosts = filter_properties.get('group_hosts')

        for i in xrange(num_hosts):
            if hosts[i].host in group_hosts:
                for j in xrange(num_instances):
                    self.variables.append([var_matrix[i][j]])
                    self.coefficients.append([1])
                    self.constants.append(0)
                    self.operators.append('==')
            else:
                self.variables.append(
                        [var_matrix[i][j] for j in range(num_instances)])
                self.coefficients.append(
                        [1 for j in range(num_instances)])
                self.constants.append(1)
                self.operators.append('<=')
