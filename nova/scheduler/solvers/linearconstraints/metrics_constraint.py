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

from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging
from nova.scheduler.solvers import linearconstraints
from nova.scheduler import utils

LOG = logging.getLogger(__name__)

CONF = cfg.CONF
CONF.import_opt('weight_setting',
                'nova.scheduler.weights.metrics',
                group='metrics')


class MetricsConstraint(linearconstraints.BaseLinearConstraint):
    """This constraint is used to filter out those hosts which don't have 
    the corresponding metrics so these the metrics weigher won't fail due 
    to these hosts.
    """

    # The linear constraint should be formed as:
    # coeff_matrix * var_matrix' (operator) (constants)
    # where (operator) is ==, >, >=, <, <=, !=, etc.
    # For convenience, the (constants) is merged into left-hand-side,
    # thus the right-hand-side is 0.

    def __init__(self):
        super(MetricsConstraint, self).__init__()
        opts = utils.parse_options(CONF.metrics.weight_setting,
                                   sep='=',
                                   converter=float,
                                   name="metrics.weight_setting")
        self.keys = [x[0] for x in opts]

    def get_coefficient_vectors(self, variables, hosts, instance_uuids,
                                request_spec, filter_properties):
        coefficient_vectors = []
        for host in hosts:
            unavail = [i for i in self.keys if i not in host.metrics]
            if unavail:
                LOG.debug(_("%(host_state)s does not have the following "
                        "metrics: %(metrics)s"),
                        {'host_state': host,
                        'metrics': ', '.join(unavail)})
            if len(unavail) == 0:
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
