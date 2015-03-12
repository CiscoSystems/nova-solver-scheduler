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
CONF.import_opt('cpu_allocation_ratio', 'nova.scheduler.filters.core_filter')

LOG = logging.getLogger(__name__)


class VcpuConstraint(constraints.BaseLinearConstraint):
    """Constraint of the total vcpu demand acceptable on each host."""

    def _generate_components(self, variables, hosts, filter_properties):
        num_hosts = len(hosts)
        num_instances = filter_properties.get('num_instances')

        var_matrix = variables.host_instacne_adjacency_matrix

        # get requested vcpus
        instance_type = filter_properties.get('instance_type')
        if not instance_type:
            requested_vcpus = 0
        else:
            instance_vcpus = instance_type['vcpus']

        for i in xrange(num_hosts):
            # get available vcpus
            if not hosts[i].vcpus_total:
                vcpus_total = 0
                LOG.warn(_("VCPUs of %(host)s not set; assuming CPU "
                            "collection broken."), {'host': hosts[i]})
            else:
                vcpus_total = hosts[i].vcpus_total * CONF.cpu_allocation_ratio
                usable_vcpus = vcpus_total - hosts[i].vcpus_used

            if usable_vcpus < requested_vcpus:
                for j in xrange(num_instances):
                    self.variables.append([var_matrix[i][j]])
                    self.coefficients.append([1])
                    self.constants.append(0)
                    self.operators.append('==')
                LOG.debug(_("%(host)s does not have %(requested)s usable "
                            "vcpus, it only has %(usable)s usable vcpus."),
                            {'host': hosts[i],
                            'requested': requested_vcpus,
                            'usable': usable_vcpus})
            else:
                self.variables.append(
                        [var_matrix[i][j] for j in range(num_instances)])
                self.coefficients.append(
                        [requested_vcpus for j in range(num_instances)])
                self.constants.append(usable_vcpus)
                self.operators.append('<=')

            if vcpus_total > 0:
                hosts[i].limits['vcpu'] = vcpus_total
