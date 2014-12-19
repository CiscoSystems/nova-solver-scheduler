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


class AggregateMultitenancyIsolation(
        linearconstraints.BaseLinearConstraint):
    """Isolate tenants in specific aggregates."""

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
        """If a host is in an aggregate that has the metadata key
        "filter_tenant_id" it can only create instances from that tenant(s).
        A host can be in different aggregates.

        If a host doesn't belong to an aggregate with the metadata key
        "filter_tenant_id" it can create instances from all tenants.
        """

        coefficient_vectors = []

        image_props = request_spec.get(
                        'instance_properties', {}).get('project_id')

        for host in hosts:
            aggregates_stats = host.host_aggregates_stats
            host_passes = True
            for aggregate in aggregates_stats.values():
                aggregate_metadata = aggregate.get('metadata', {})
                filter_tenant_id = aggregate_metadata.get('filter_tenant_id')
                if filter_tenant_id and tenant_id not in filter_tenant_id:
                    host_passes = False
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
