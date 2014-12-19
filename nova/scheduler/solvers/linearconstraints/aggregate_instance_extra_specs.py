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
from nova.scheduler.filters import extra_specs_ops

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

_SCOPE = 'aggregate_instance_extra_specs'


class AggregateInstanceExtraSpecs(
        linearconstraints.BaseLinearConstraint):
    """AggregateInstanceExtraSpecs works with InstanceType records."""

    # The linear constraint should be formed as:
    # coeff_matrix * var_matrix' (operator) constant_vector
    # where (operator) is ==, >, >=, <, <=, !=, etc.
    # For convenience, the constant_vector is merged into left-hand-side,
    # thus the right-hand-side is always 0.

    def __init__(self):
        self.compute_api = compute.API()
        [self.num_hosts, self.num_instances] = self._get_host_instance_nums(
                                        hosts, instance_uuids, request_spec)

    def _get_host_instance_nums(self, hosts, instance_uuids, request_spec):
        """This method calculates number of hosts and instances."""
        num_hosts = len(hosts)
        if instance_uuids:
            num_instances = len(instance_uuids)
        else:
            num_instances = request_spec.get('num_instances', 1)
        return [num_hosts, num_instances]

    def get_coefficient_vectors(self, variables, hosts, instance_uuids,
                                request_spec, filter_properties):
        """Return a list of hosts that can create instance_type

        Check that the extra specs associated with the instance type match
        the metadata provided by aggregates.  If not present return False.
        """
        coefficient_vectors = []

        instance_type = filter_properties.get('instance_type')
        if 'extra_specs' not in instance_type:
            coefficient_vectors = [[0 for j in range(self.num_instances)]
                                    for i in range(self.num_hosts)]
            return coefficient_vectors

        for host in hosts:
            aggregates_stats = host.host_aggregates_stats
            host_passes = True
            for aggregate in aggregates_stats.values():
                aggregate_metadata = aggregate.get('metadata', {})
                for key, req in instance_type['extra_specs'].iteritems():
                    # Either not scope format, 
                    # or aggregate_instance_extra_specs scope
                    scope = key.split(':', 1)
                    if len(scope) > 1:
                        if scope[0] != _SCOPE:
                            continue
                        else:
                            del scope[0]
                    key = scope[0]
                    aggregate_vals = aggregate_metadata.get(key, None)
                    if not aggregate_vals:
                        host_passes = False
                        break
                    for val in aggregate_vals:
                        if exrta_specs_ops.match(val, req):
                            break
                        else:
                            host_passes = False
                            break
                if not host_passes:
                    break
            if not host_passes:
                coefficient_vectors.append(
                                    [1 for j in range(self.num_instances)])
            else:
                coefficient_vectors.append(
                                    [0 for j in range(self.num_instances)])
            
        return coefficient_vectors

    def get_variable_vectors(self,variables,hosts,instance_uuids,request_spec,filter_properties):
        variable_vectors = []
        variable_vectors = [[variables[i][j] for j in range(
                        self.num_instances)] for i in range(self.num_hosts)]
        return variable_vectors

    def get_operations(self,variables,hosts,instance_uuids,request_spec,filter_properties):
        operations = [(lambda x: x==0) for i in range(self.num_hosts)]
        return operations
