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

from nova import db
from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging
from nova.scheduler.solvers import linearconstraints

LOG = logging.getLogger(__name__)


class TypeAffinityConstraint(linearconstraints.BaseLinearConstraint):
    """TypeAffinityConstraint doesn't allow more then one VM type per host.

    Note: this works best with ram_weight_multiplier
    (spread) set to 1 (default).
    """

    # The linear constraint should be formed as:
    # coeff_matrix * var_matrix' (operator) (constants)
    # where (operator) is ==, >, >=, <, <=, !=, etc.
    # For convenience, the (constants) is merged into left-hand-side,
    # thus the right-hand-side is 0.

    def get_coefficient_vectors(self, variables, hosts, instance_uuids,
                                request_spec, filter_properties):
        instance_type = filter_properties.get('instance_type')
        context = filter_properties['context'].elevated()

        coefficient_vectors = []
        for host in hosts:
            instances_other_type = db.instance_get_all_by_host_and_not_type(
                    context, host.host, instance_type['id'])
            if len(instances_other_type) == 0:
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
