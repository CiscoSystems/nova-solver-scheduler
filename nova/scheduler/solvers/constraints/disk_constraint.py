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
CONF.import_opt('disk_allocation_ratio', 'nova.scheduler.filters.disk_filter')

LOG = logging.getLogger(__name__)


class DiskConstraint(constraints.BaseLinearConstraint):
    """Constraint of the maximum total disk demand acceptable on each host."""

    def _generate_components(self, variables, hosts, filter_properties):
        num_hosts = len(hosts)
        num_instances = filter_properties.get('num_instances')

        var_matrix = variables.host_instance_matrix

        # get requested disk
        instance_type = filter_properties.get('instance_type') or {}
        requested_disk = (1024 * (instance_type.get('root_gb', 0) +
                                  instance_type.get('ephemeral_gb', 0)) +
                                  instance_type.get('swap', 0))
        for inst_type_key in ['root_gb', 'ephemeral_gb', 'swap']:
            if inst_type_key not in instance_type:
                LOG.warn(_("Disk information of requested instances\' %s "
                        "is incomplete, use 0 as the requested %s size.") %
                        (inst_type_key, inst_type_key))
        if requested_disk <= 0:
            LOG.warn(_("DiskConstraint is skipped because requested "
                        "instance disk size is 0 or invalid."))
            return

        for i in xrange(num_hosts):
            # get usable disk
            free_disk_mb = hosts[i].free_disk_mb
            total_usable_disk_mb = hosts[i].total_usable_disk_gb * 1024
            disk_mb_limit = total_usable_disk_mb * CONF.disk_allocation_ratio
            used_disk_mb = total_usable_disk_mb - free_disk_mb
            usable_disk_mb = disk_mb_limit - used_disk_mb

            acceptable_num_instances = int(usable_disk_mb / requested_disk)
            if acceptable_num_instances < num_instances:
                for j in xrange(acceptable_num_instances, num_instances):
                    self.variables.append([var_matrix[i][j]])
                    self.coefficients.append([1])
                    self.constants.append(0)
                    self.operators.append('==')

            LOG.debug(_("%(host)s can accept %(num)s requested instances "
                        "according to DiskConstraint."),
                        {'host': hosts[i],
                        'num': acceptable_num_instances})

            disk_gb_limit = disk_mb_limit / 1024
            hosts[i].limits['disk_gb'] = disk_gb_limit
