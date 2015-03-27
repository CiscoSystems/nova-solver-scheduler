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

"""Test case for solver scheduler RAM cost."""

from nova import context
from nova.openstack.common.fixture import mockpatch
from nova.scheduler import solvers
from nova.scheduler.solvers import costs
from nova.scheduler.solvers.costs import ram_cost
from nova import test
from nova.tests import matchers
from nova.tests.scheduler import solver_scheduler_fakes as fakes


class TestRamCost(test.NoDBTestCase):
    def setUp(self):
        super(TestRamCost, self).setUp()
        self.context = context.RequestContext('fake_usr', 'fake_proj')
        self.useFixture(mockpatch.Patch('nova.db.compute_node_get_all',
                return_value=fakes.COMPUTE_NODES[0:5]))
        self.host_manager = fakes.FakeSolverSchedulerHostManager()
        self.cost_handler = costs.CostHandler()
        self.cost_classes = self.cost_handler.get_matching_classes(
                ['nova.scheduler.solvers.costs.ram_cost.RamCost'])

    def _get_all_hosts(self):
        ctxt = context.get_admin_context()
        return self.host_manager.get_all_host_states(ctxt)

    def test_ram_cost_multiplier_1(self):
        self.flags(ram_cost_multiplier=0.5, group='solver_scheduler')
        self.assertEqual(0.5, ram_cost.RamCost().cost_multiplier())

    def test_ram_cost_multiplier_2(self):
        self.flags(ram_cost_multiplier=(-2), group='solver_scheduler')
        self.assertEqual((-2), ram_cost.RamCost().cost_multiplier())

    def test_ram_cost_get_components(self):
        # the host.free_ram_mb values of these fake hosts are supposed to be:
        # 512, 1024, 3072, 8192
        fake_hosts = self._get_all_hosts()
        # FIXME: ideally should mock get_hosts_stripping_forced_and_ignored()
        fake_hosts = list(fake_hosts)
        # the hosts order may be arbitrary, here we manually order them
        # which is for convenience of testings
        tmp = []
        for i in range(len(fake_hosts)):
            for fh in fake_hosts:
                if fh.host == 'host%s' % (i + 1):
                    tmp.append(fh)
        fake_hosts = tmp
        fake_variables = solvers.BaseVariables()
        fake_variables.host_instance_matrix = [
                ['h0i0', 'h0i1', 'h0i2'],
                ['h1i0', 'h1i1', 'h1i2'],
                ['h2i0', 'h2i1', 'h2i2'],
                ['h3i0', 'h3i1', 'h3i2']]
        fake_filter_properties = {
                'context': self.context.elevated(),
                'num_instances': 3,
                'instance_type': {'memory_mb': 128},
                'instance_uuids': ['fake_uuid_%s' % x for x in range(3)]}

        fake_cost = self.cost_classes[0]()

        expected_cost_vars = [
                'h0i0', 'h0i1', 'h0i2', 'h1i0', 'h1i1', 'h1i2',
                'h2i0', 'h2i1', 'h2i2', 'h3i0', 'h3i1', 'h3i2']
        expected_cost_coeffs = [
                -512, -384, -256, -1024, -896, -768,
                -3072, -2944, -2816, -8192, -8064, -7936]

        cost_vars, cost_coeffs = fake_cost.get_components(
                        fake_variables, fake_hosts, fake_filter_properties)
        self.assertEqual(expected_cost_vars, cost_vars)
        self.assertEqual(expected_cost_coeffs, cost_coeffs)
