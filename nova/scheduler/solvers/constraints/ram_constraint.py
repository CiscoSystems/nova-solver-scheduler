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
from nova.scheduler.solvers import constraints

CONF = cfg.CONF
CONF.import_opt('ram_allocation_ratio', 'nova.scheduler.filters.ram_filter')

LOG = logging.getLogger(__name__)

class RamConstraint(constraints.BaseLinearConstraint):
    """Constraint of the total ram demand acceptable on each host."""

    def _get_ram_allocation_ratio(self, host_state, filter_properties):
        return CONF.ram_allocation_ratio

    def _generate_components(self, variables, hosts, filter_properties):
        num_hosts = len(hosts)
        num_instances = filter_properties.get('num_instances')

        var_matrix = variables.host_instance_matrix

        # get requested ram
        instance_type = filter_properties.get('instance_type') or {}
        requested_ram = instance_type.get('memory_mb', 0)
        if 'memory_mb' not in instance_type:
            LOG.warn(_("No information about requested instances\' RAM size "
                    "was found, default value (0) is used."))
        if requested_ram <= 0:
            LOG.warn(_("RamConstraint is skipped because requested "
                        "instance RAM size is 0 or invalid."))
            return

        for i in xrange(num_hosts):
            ram_allocation_ratio = self._get_ram_allocation_ratio(
                                                hosts[i], filter_properties)
            # get available ram
            free_ram_mb = hosts[i].free_ram_mb
            total_usable_ram_mb = hosts[i].total_usable_ram_mb
            memory_mb_limit = total_usable_ram_mb * ram_allocation_ratio
            used_ram_mb = total_usable_ram_mb - free_ram_mb
            usable_ram = memory_mb_limit - used_ram_mb

            acceptable_num_instances = int(usable_ram / requested_ram)
            if acceptable_num_instances < num_instances:
                for j in xrange(acceptable_num_instances, num_instances):
                    self.variables.append([var_matrix[i][j]])
                    self.coefficients.append([1])
                    self.constants.append(0)
                    self.operators.append('==')

            LOG.debug(_("%(host)s can accept %(num)s requested instances "
                        "according to RamConstraint."),
                        {'host': hosts[i],
                        'num': acceptable_num_instances})

            hosts[i].limits['memory_mb'] = memory_mb_limit
