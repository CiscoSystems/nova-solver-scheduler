# Copyright (c) 2011-2012 OpenStack Foundation
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

LOG = logging.getLogger(__name__)

CONF = cfg.CONF
CONF.import_opt('isolated_images',
                'nova.scheduler.filters.isolated_hosts_filter')
CONF.import_opt('isolated_hosts',
                'nova.scheduler.filters.isolated_hosts_filter')
CONF.import_opt('restrict_isolated_hosts_to_isolated_images',
                'nova.scheduler.filters.isolated_hosts_filter')


class IsolatedHostsConsrtaint(linearconstraints.BaseLinearConstraint):
    """Keep specified images to selected hosts."""

    def get_coefficient_vectors(self, variables, hosts, instance_uuids,
                                request_spec, filter_properties):
        """Result Matrix with 'restrict_isolated_hosts_to_isolated_images' set
        to True:
                     | isolated_image | non_isolated_image
        -------------+----------------+-------------------
        iso_host     |    True        |     False
        non_iso_host |    False       |      True

        Result Matrix with 'restrict_isolated_hosts_to_isolated_images' set
        to False:
                     | isolated_image | non_isolated_image
        -------------+----------------+-------------------
        iso_host     |    True        |      True
        non_iso_host |    False       |      True

        """
        isolated_hosts = CONF.isolated_hosts
        isolated_images = CONF.isolated_images
        restrict_isolated_hosts_to_isolated_images = (CONF.
                                   restrict_isolated_hosts_to_isolated_images)
        spec = filter_properties.get('request_spec', {})
        props = spec.get('instance_properties', {})
        image_ref = props.get('image_ref')

        coefficient_vectors = []
        for host in hosts:
            host_passes = True
            if not isolated_images:
                host_passes = (
                        not restrict_isolated_hosts_to_isolated_images) or (
                        host.host not in isolated_hosts)
            else:
                image_isolated = image_ref in isolated_images
                host_isolated = host.host in isolated_hosts
                if restrict_isolated_hosts_to_isolated_images:
                    host_passes = (image_isolated == host_isolated)
                else:
                    host_passes = (not image_isolated) or host_isolated
            if host_passes:
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
