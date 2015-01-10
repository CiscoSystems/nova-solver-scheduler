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
from nova.scheduler.linearconstraints import extra_specs_ops


LOG = logging.getLogger(__name__)


class ComputeCapabilitiesConstraint(linearconstraints.BaseLinearConstraint):
    """Hard-coded to work with InstanceType records."""

    def _satisfies_extra_specs(self, host_state, instance_type):
        """Check that the host_state provided by the compute service
        satisfy the extra specs associated with the instance type.
        """
        if 'extra_specs' not in instance_type:
            return True

        for key, req in instance_type['extra_specs'].iteritems():
            # Either not scope format, or in capabilities scope
            scope = key.split(':')
            if len(scope) > 1:
                if scope[0] != "capabilities":
                    continue
                else:
                    del scope[0]
            cap = host_state
            for index in range(0, len(scope)):
                try:
                    if not isinstance(cap, dict):
                        if getattr(cap, scope[index], None) is None:
                            # If can't find, check stats dict
                            cap = cap.stats.get(scope[index], None)
                        else:
                            cap = getattr(cap, scope[index], None)
                    else:
                        cap = cap.get(scope[index], None)
                except AttributeError:
                    return False
                if cap is None:
                    return False
            if not extra_specs_ops.match(str(cap), req):
                LOG.debug(_("extra_spec requirement '%(req)s' does not match "
                    "'%(cap)s'"), {'req': req, 'cap': cap})
                return False
        return True

    def get_coefficient_vectors(self, variables, hosts, instance_uuids,
                                request_spec, filter_properties):
        coefficient_vectors = []
        for host in hosts:
            instance_type = filter_properties.get('instance_type')
            if not self._satisfies_extra_specs(host, instance_type):
                coefficient_vectors.append([1
                        for j in range(self.num_instances)])
            else:
                coefficient_vectors.append([0
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
