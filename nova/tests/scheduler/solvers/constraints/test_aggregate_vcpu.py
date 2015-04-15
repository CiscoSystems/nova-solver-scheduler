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

import mock

from nova import context
from nova.scheduler import solvers
from nova.scheduler.solvers.constraints import aggregate_vcpu
from nova import test
from nova.tests.scheduler import solver_scheduler_fakes as fakes


class TestAggregateVcpuConstraint(test.NoDBTestCase):
    def setUp(self):
        super(TestAggregateVcpuConstraint, self).setUp()
        self.constraint_cls = aggregate_vcpu.AggregateVcpuConstraint
        self.context = context.RequestContext('fake', 'fake')
        self._generate_fake_constraint_input()

    def _generate_fake_constraint_input(self):
        self.fake_variables = solvers.BaseVariables()
        self.fake_variables.host_instance_matrix = [
                ['h0i0', 'h0i1'],
                ['h1i0', 'h1i1'],
                ['h2i0', 'h2i1']]
        self.fake_filter_properties = {
                'context': self.context,
                'instance_type': {'vcpus': 2},
                'instance_uuids': ['fake_uuid_%s' % x for x in range(2)],
                'num_instances': 2}
        host1 = fakes.FakeSolverSchedulerHostState('host1', 'node1',
                {'vcpus_total': 16, 'vcpus_used': 16})
        host2 = fakes.FakeSolverSchedulerHostState('host2', 'node1',
                {'vcpus_total': 16, 'vcpus_used': 16})
        host3 = fakes.FakeSolverSchedulerHostState('host3', 'node1',
                {'vcpus_total': 16, 'vcpus_used': 16})
        self.fake_hosts = [host1, host2, host3]

    @mock.patch('nova.db.aggregate_metadata_get_by_host')
    def test_aggregate_vcpu_get_components(self, agg_mock):
        self.flags(cpu_allocation_ratio=1.0)

        def _agg_mock_side_effect(*args, **kwargs):
            if args[1] == 'host1':
                return {'cpu_allocation_ratio': set(['1.0', '2.0'])}
            if args[1] == 'host2':
                return {'cpu_allocation_ratio': set(['3.0'])}
            if args[1] == 'host3':
                return {'cpu_allocation_ratio': set()}
        agg_mock.side_effect = _agg_mock_side_effect

        expected_cons_vars = [
                ['h0i0'], ['h0i1'], ['h2i0'], ['h2i1']]
        expected_cons_coeffs = [[1], [1], [1], [1]]
        expected_cons_consts = [0, 0, 0, 0]
        expected_cons_ops = ['==', '==', '==', '==']
        cons_vars, cons_coeffs, cons_consts, cons_ops = (
                self.constraint_cls().get_components(self.fake_variables,
                self.fake_hosts, self.fake_filter_properties))
        self.assertEqual(expected_cons_vars, cons_vars)
        self.assertEqual(expected_cons_coeffs, cons_coeffs)
        self.assertEqual(expected_cons_consts, cons_consts)
        self.assertEqual(expected_cons_ops, cons_ops)
