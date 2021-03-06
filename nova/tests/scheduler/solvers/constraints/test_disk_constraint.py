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

from nova.scheduler import solvers
from nova.scheduler.solvers.constraints import disk_constraint
from nova import test
from nova.tests.scheduler import solver_scheduler_fakes as fakes


class TestDiskConstraint(test.NoDBTestCase):

    def setUp(self):
        super(TestDiskConstraint, self).setUp()
        self.constraint_cls = disk_constraint.DiskConstraint
        self._generate_fake_constraint_input()

    def _generate_fake_constraint_input(self):
        self.fake_variables = solvers.BaseVariables()
        self.fake_variables.host_instance_matrix = [
                ['h0i0', 'h0i1'],
                ['h1i0', 'h1i1'],
                ['h2i0', 'h2i1']]
        self.fake_filter_properties = {
                'instance_type': {'root_gb': 1, 'ephemeral_gb': 1,
                                    'swap': 512},
                'instance_uuids': ['fake_uuid_%s' % x for x in range(2)],
                'num_instances': 2}
        host1 = fakes.FakeSolverSchedulerHostState('host1', 'node1',
                {'free_disk_mb': 1 * 1024, 'total_usable_disk_gb': 2})
        host2 = fakes.FakeSolverSchedulerHostState('host2', 'node1',
                {'free_disk_mb': 10 * 1024, 'total_usable_disk_gb': 12})
        host3 = fakes.FakeSolverSchedulerHostState('host3', 'node1',
                {'free_disk_mb': 1 * 1024, 'total_usable_disk_gb': 6})
        self.fake_hosts = [host1, host2, host3]

    def test_disk_constraint_get_components(self):
        self.flags(disk_allocation_ratio=1.0)
        expected_cons_vars = [['h0i0'], ['h0i1'], ['h2i0'], ['h2i1']]
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

    def test_disk_constraint_get_components_oversubscribe(self):
        self.flags(disk_allocation_ratio=2.0)
        expected_cons_vars = [['h0i1']]
        expected_cons_coeffs = [[1]]
        expected_cons_consts = [0]
        expected_cons_ops = ['==']
        cons_vars, cons_coeffs, cons_consts, cons_ops = (
                self.constraint_cls().get_components(self.fake_variables,
                self.fake_hosts, self.fake_filter_properties))
        self.assertEqual(expected_cons_vars, cons_vars)
        self.assertEqual(expected_cons_coeffs, cons_coeffs)
        self.assertEqual(expected_cons_consts, cons_consts)
        self.assertEqual(expected_cons_ops, cons_ops)
        self.assertEqual(2 * 2.0, self.fake_hosts[0].limits['disk_gb'])
        self.assertEqual(12 * 2.0, self.fake_hosts[1].limits['disk_gb'])
        self.assertEqual(6 * 2.0, self.fake_hosts[2].limits['disk_gb'])
