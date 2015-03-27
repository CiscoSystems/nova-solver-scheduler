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

"""
RAM Cost.  Calculate instance placement costs by hosts' RAM usage.

The default is to spread instances across all hosts evenly.  If you prefer
stacking, you can set the 'ram_cost_multiplier' option to a positive
number and the cost has the opposite effect of the default.
"""

from oslo.config import cfg

from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging
from nova.scheduler.solvers import costs as solver_costs

ram_cost_opts = [
        cfg.FloatOpt('ram_cost_multiplier',
                     default=1.0,
                     help='Multiplier used for ram costs. Negative '
                          'numbers mean to spread vs stack.'),
]

CONF = cfg.CONF
CONF.register_opts(ram_cost_opts, group='solver_scheduler')

LOG = logging.getLogger(__name__)


class RamCost(solver_costs.BaseLinearCost):

    def cost_multiplier(self):
        return CONF.solver_scheduler.ram_cost_multiplier

    def _generate_components(self, variables, hosts, filter_properties):
        num_hosts = len(hosts)
        num_instances = filter_properties.get('num_instances')

        instance_type = filter_properties.get('instance_type') or {}
        requested_ram = instance_type.get('memory_mb', 0)
        if 'memory_mb' not in instance_type:
            LOG.warn(_("No information about requested instances\' RAM size "
                    "was found, default value (0) is used."))

        var_matrix = variables.host_instance_matrix
        self.variables = [var_matrix[i][j] for i in range(num_hosts)
                                            for j in range(num_instances)]

        coeff_matrix = [[(-hosts[i].free_ram_mb + requested_ram * (j + 1))
                    for j in range(num_instances)] for i in range(num_hosts)]
        self.coefficients = [coeff_matrix[i][j] for i in range(num_hosts)
                                                for j in range(num_instances)]
