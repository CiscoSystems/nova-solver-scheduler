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


class TestMetricsCost(test.NoDBTestCase):
    def setUp(self):
        super(TestMetricsCost, self).setUp()
        self.context = context.RequestContext('fake_usr', 'fake_proj')
        self.useFixture(mockpatch.Patch('nova.db.compute_node_get_all',
                return_value=fakes.COMPUTE_NODES_METRICS))
        self.host_manager = fakes.FakeSolverSchedulerHostManager()
        self.cost_handler = costs.CostHandler()
        self.cost_classes = self.cost_handler.get_matching_classes(
                ['nova.scheduler.solvers.costs.metrics_cost.MetricsCost'])

    def _get_all_hosts(self):
        ctxt = context.get_admin_context()
        return self.host_manager.get_all_host_states(ctxt)

    def _get_fake_cost_inputs(self):
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
                'instance_uuids': ['fake_uuid_%s' % x for x in range(3)]}
        return (fake_hosts, fake_variables, fake_filter_properties)

    def test_metrics_cost_multiplier_1(self):
        self.flags(ram_cost_multiplier=0.5, group='solver_scheduler')
        self.assertEqual(0.5, ram_cost.RamCost().cost_multiplier())

    def test_metrics_cost_multiplier_2(self):
        self.flags(ram_cost_multiplier=(-2), group='solver_scheduler')
        self.assertEqual((-2), ram_cost.RamCost().cost_multiplier())

    def test_metrics_cost_get_components_single_resource(self):
        # host1: foo=512
        # host2: foo=1024
        # host3: foo=3072
        # host4: foo=8192
        # so, host4 should win:
        setting = ['foo=1']
        self.flags(weight_setting=setting, group='metrics')

        fake_hosts, fake_variables, fake_filter_properties = (
                                                self._get_fake_cost_inputs())
        fake_hosts = fake_hosts[0:4]

        fake_cost = self.cost_classes[0]()

        expected_cost_vars = [
                'h0i0', 'h0i1', 'h0i2', 'h1i0', 'h1i1', 'h1i2',
                'h2i0', 'h2i1', 'h2i2', 'h3i0', 'h3i1', 'h3i2']
        #expected_cost_coeffs = [
        #        -512, -512, -512, -1024, -1024, -1024,
        #        -3072, -3072, -3072, -8192, -8192, -8192]
        expected_cost_coeffs = [
                -0.0625, -0.0625, -0.0625, -0.125, -0.125, -0.125,
                -0.375, -0.375, -0.375, -1.0, -1.0, -1.0]

        cost_vars, cost_coeffs = fake_cost.get_components(
                        fake_variables, fake_hosts, fake_filter_properties)
        round_cost_values = lambda x: round(x, 4)
        expected_cost_coeffs = map(round_cost_values, expected_cost_coeffs)
        cost_coeffs = map(round_cost_values, cost_coeffs)
        self.assertEqual(expected_cost_vars, cost_vars)
        self.assertEqual(expected_cost_coeffs, cost_coeffs)

    def test_metrics_cost_get_components_multiple_resource(self):
        # host1: foo=512,  bar=1
        # host2: foo=1024, bar=2
        # host3: foo=3072, bar=1
        # host4: foo=8192, bar=0
        # so, host2 should win:
        setting = ['foo=0.0001', 'bar=1']
        self.flags(weight_setting=setting, group='metrics')

        fake_hosts, fake_variables, fake_filter_properties = (
                                                self._get_fake_cost_inputs())
        fake_hosts = fake_hosts[0:4]

        fake_cost = self.cost_classes[0]()

        expected_cost_vars = [
                'h0i0', 'h0i1', 'h0i2', 'h1i0', 'h1i1', 'h1i2',
                'h2i0', 'h2i1', 'h2i2', 'h3i0', 'h3i1', 'h3i2']
        #expected_cost_coeffs = [
        #        -1.0512, -1.0512, -1.0512, -2.1024, -2.1024, -2.1024,
        #        -1.3072, -1.3072, -1.3072, -0.8192, -0.8192, -0.8192]
        expected_cost_coeffs = [
                -0.5, -0.5, -0.5, -1.0, -1.0, -1.0,
                -0.6218, -0.6218, -0.6218, -0.3896, -0.3896, -0.3896]

        cost_vars, cost_coeffs = fake_cost.get_components(
                        fake_variables, fake_hosts, fake_filter_properties)
        round_cost_values = lambda x: round(x, 4)
        expected_cost_coeffs = map(round_cost_values, expected_cost_coeffs)
        cost_coeffs = map(round_cost_values, cost_coeffs)
        self.assertEqual(expected_cost_vars, cost_vars)
        self.assertEqual(expected_cost_coeffs, cost_coeffs)

    def test_metrics_cost_get_components_single_resource_negative_ratio(self):
        # host1: foo=512
        # host2: foo=1024
        # host3: foo=3072
        # host4: foo=8192
        # so, host1 should win:
        setting = ['foo=-1']
        self.flags(weight_setting=setting, group='metrics')

        fake_hosts, fake_variables, fake_filter_properties = (
                                                self._get_fake_cost_inputs())
        fake_hosts = fake_hosts[0:4]

        fake_cost = self.cost_classes[0]()

        expected_cost_vars = [
                'h0i0', 'h0i1', 'h0i2', 'h1i0', 'h1i1', 'h1i2',
                'h2i0', 'h2i1', 'h2i2', 'h3i0', 'h3i1', 'h3i2']
        #expected_cost_coeffs = [
        #        512, 512, 512, 1024, 1024, 1024,
        #        3072, 3072, 3072, 8192, 8192, 8192]
        expected_cost_coeffs = [
                0.0625, 0.0625, 0.0625, 0.125, 0.125, 0.125,
                0.375, 0.375, 0.375, 1.0, 1.0, 1.0]

        cost_vars, cost_coeffs = fake_cost.get_components(
                        fake_variables, fake_hosts, fake_filter_properties)
        round_cost_values = lambda x: round(x, 4)
        expected_cost_coeffs = map(round_cost_values, expected_cost_coeffs)
        cost_coeffs = map(round_cost_values, cost_coeffs)
        self.assertEqual(expected_cost_vars, cost_vars)
        self.assertEqual(expected_cost_coeffs, cost_coeffs)

    def test_metrics_cost_get_components_multiple_resource_missing_ratio(self):
        # host1: foo=512,  bar=1
        # host2: foo=1024, bar=2
        # host3: foo=3072, bar=1
        # host4: foo=8192, bar=0
        # so, host4 should win:
        setting = ['foo=0.0001', 'bar']
        self.flags(weight_setting=setting, group='metrics')

        fake_hosts, fake_variables, fake_filter_properties = (
                                                self._get_fake_cost_inputs())
        fake_hosts = fake_hosts[0:4]

        fake_cost = self.cost_classes[0]()

        expected_cost_vars = [
                'h0i0', 'h0i1', 'h0i2', 'h1i0', 'h1i1', 'h1i2',
                'h2i0', 'h2i1', 'h2i2', 'h3i0', 'h3i1', 'h3i2']
        #expected_cost_coeffs = [
        #        -0.0512, -0.0512, -0.0512, -0.1024, -0.1024, -0.1024,
        #        -0.3072, -0.3072, -0.3072, -0.8192, -0.8192, -0.8192]
        expected_cost_coeffs = [
                -0.0625, -0.0625, -0.0625, -0.125, -0.125, -0.125,
                -0.375, -0.375, -0.375, -1.0, -1.0, -1.0]

        cost_vars, cost_coeffs = fake_cost.get_components(
                        fake_variables, fake_hosts, fake_filter_properties)
        round_cost_values = lambda x: round(x, 4)
        expected_cost_coeffs = map(round_cost_values, expected_cost_coeffs)
        cost_coeffs = map(round_cost_values, cost_coeffs)
        self.assertEqual(expected_cost_vars, cost_vars)
        self.assertEqual(expected_cost_coeffs, cost_coeffs)

    def test_metrics_cost_get_components_multiple_resource_wrong_ratio(self):
        # host1: foo=512,  bar=1
        # host2: foo=1024, bar=2
        # host3: foo=3072, bar=1
        # host4: foo=8192, bar=0
        # so, host4 should win:
        setting = ['foo=0.0001', 'bar = 2.0t']
        self.flags(weight_setting=setting, group='metrics')

        fake_hosts, fake_variables, fake_filter_properties = (
                                                self._get_fake_cost_inputs())
        fake_hosts = fake_hosts[0:4]

        fake_cost = self.cost_classes[0]()

        expected_cost_vars = [
                'h0i0', 'h0i1', 'h0i2', 'h1i0', 'h1i1', 'h1i2',
                'h2i0', 'h2i1', 'h2i2', 'h3i0', 'h3i1', 'h3i2']
        #expected_cost_coeffs = [
        #        -0.0512, -0.0512, -0.0512, -0.1024, -0.1024, -0.1024,
        #        -0.3072, -0.3072, -0.3072, -0.8192, -0.8192, -0.8192]
        expected_cost_coeffs = [
                -0.0625, -0.0625, -0.0625, -0.125, -0.125, -0.125,
                -0.375, -0.375, -0.375, -1.0, -1.0, -1.0]

        cost_vars, cost_coeffs = fake_cost.get_components(
                        fake_variables, fake_hosts, fake_filter_properties)
        round_cost_values = lambda x: round(x, 4)
        expected_cost_coeffs = map(round_cost_values, expected_cost_coeffs)
        cost_coeffs = map(round_cost_values, cost_coeffs)
        self.assertEqual(expected_cost_vars, cost_vars)
        self.assertEqual(expected_cost_coeffs, cost_coeffs)

    def test_metrics_cost_get_components_metric_not_found(self):
        # host3: foo=3072, bar=1
        # host4: foo=8192, bar=0
        # host5: foo=768, bar=0, zot=1
        # host6: foo=2048, bar=0, zot=2
        setting = ['foo=0.0001', 'zot=-2']
        self.flags(weight_setting=setting, group='metrics')

        fake_hosts, fake_variables, fake_filter_properties = (
                                                self._get_fake_cost_inputs())
        fake_hosts = fake_hosts[2:6]

        fake_cost = self.cost_classes[0]()

        expected_cost_vars = [
                'h0i0', 'h0i1', 'h0i2', 'h1i0', 'h1i1', 'h1i2',
                'h2i0', 'h2i1', 'h2i2', 'h3i0', 'h3i1', 'h3i2']
        #expected_cost_coeffs = [
        #        5.6672, 5.6672, 5.6672, 5.6672, 5.6672, 5.6672,
        #        1.9232, 1.9232, 1.9232, 3.7952, 3.7952, 3.7952]
        expected_cost_coeffs = [
                1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                0.3394, 0.3394, 0.3394, 0.6697, 0.6697, 0.6697]

        cost_vars, cost_coeffs = fake_cost.get_components(
                        fake_variables, fake_hosts, fake_filter_properties)
        round_cost_values = lambda x: round(x, 4)
        expected_cost_coeffs = map(round_cost_values, expected_cost_coeffs)
        cost_coeffs = map(round_cost_values, cost_coeffs)
        self.assertEqual(expected_cost_vars, cost_vars)
        self.assertEqual(expected_cost_coeffs, cost_coeffs)

    def test_metrics_cost_get_components_metric_not_found_in_any(self):
        # host3: foo=3072, bar=1
        # host4: foo=8192, bar=0
        # host5: foo=768, bar=0, zot=1
        # host6: foo=2048, bar=0, zot=2
        setting = ['foo=0.0001', 'non_exist_met=2']
        self.flags(weight_setting=setting, group='metrics')

        fake_hosts, fake_variables, fake_filter_properties = (
                                                self._get_fake_cost_inputs())
        fake_hosts = fake_hosts[2:6]

        fake_cost = self.cost_classes[0]()

        expected_cost_vars = [
                'h0i0', 'h0i1', 'h0i2', 'h1i0', 'h1i1', 'h1i2',
                'h2i0', 'h2i1', 'h2i2', 'h3i0', 'h3i1', 'h3i2']
        expected_cost_coeffs = [
                0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0]

        cost_vars, cost_coeffs = fake_cost.get_components(
                        fake_variables, fake_hosts, fake_filter_properties)
        self.assertEqual(expected_cost_vars, cost_vars)
        self.assertEqual(expected_cost_coeffs, cost_coeffs)

    def _check_parsing_result(self, cost, setting, results):
        self.flags(weight_setting=setting, group='metrics')
        cost._parse_setting()
        self.assertTrue(len(results) == len(cost.setting))
        for item in results:
            self.assertTrue(item in cost.setting)

    def test_metrics_cost_parse_setting(self):
        fake_cost = self.cost_classes[0]()
        self._check_parsing_result(fake_cost,
                                   ['foo=1'],
                                   [('foo', 1.0)])
        self._check_parsing_result(fake_cost,
                                   ['foo=1', 'bar=-2.1'],
                                   [('foo', 1.0), ('bar', -2.1)])
        self._check_parsing_result(fake_cost,
                                   ['foo=a1', 'bar=-2.1'],
                                   [('bar', -2.1)])
        self._check_parsing_result(fake_cost,
                                   ['foo', 'bar=-2.1'],
                                   [('bar', -2.1)])
        self._check_parsing_result(fake_cost,
                                   ['=5', 'bar=-2.1'],
                                   [('bar', -2.1)])
