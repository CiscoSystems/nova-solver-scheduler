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

from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging
from nova.scheduler.solvers import linearconstraints

LOG = logging.getLogger(__name__)


class RetryConstraint(
        linearconstraints.BaseLinearConstraint):
    """Filter out nodes that have already been attempted for scheduling
    purposes
    """

    # The linear constraint should be formed as:
    # coeff_vectors * var_vectors' (operator) (constants)
    # where (operator) is ==, >, >=, <, <=, !=, etc.
    # For convenience, the (constants) is merged into left-hand-side,
    # thus the right-hand-side is 0.

    def get_coefficient_vectors(self, variables, hosts, instance_uuids,
                                request_spec, filter_properties):
        coefficient_vectors = []
        retry = filter_properties.get('retry', None)
        if not retry:
            coefficient_vectors = [[0 for j in range(self.num_instances)]
                                    for i in range(self.num_hosts)]
            return coefficient_vectors
        attempted_hosts = retry.get('hosts', [])
        for host in hosts:
            host_key = [host.host, host.nodename]
            if host_key not in attempted_hosts:
                coefficient_vectors.append([0 for j in
                                            range(self.num_instances)])
            else:
                coefficient_vectors.append([1 for j in
                                            range(self.num_instances)])
        return coefficient_vectors

    def get_variable_vectors(self, variables, hosts, instance_uuids,
                             request_spec, filter_properties):
        # The variable_vectors[i,j] denotes the relationship between host[i]
        # and instance[j].
        variable_vectors = []
        variable_vectors = [[variables[i][j]
                            for j in range(self.num_instances)]
                            for i in range(self.num_hosts)]
        return variable_vectors

    def get_operations(self, variables, hosts, instance_uuids, request_spec,
                       filter_properties):
        operations = [(lambda x: x == 0) for i in range(self.num_hosts)]
        return operations
