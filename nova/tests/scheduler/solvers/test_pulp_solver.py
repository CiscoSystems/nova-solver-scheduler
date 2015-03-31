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

"""
Tests For Pulp-Solver.
"""

import contextlib
import mock

from nova.scheduler import solver_scheduler_host_manager as host_manager
from nova.scheduler import solvers
from nova.scheduler.solvers import constraints
from nova.scheduler.solvers import costs
from nova.scheduler.solvers import pulp_solver
from nova import solver_scheduler_exception as exception
from nova import test


class FakeCostClass1(costs.BaseLinearCost):
    def _generate_components(self, variables, hosts, filter_properties):
        num_hosts = len(hosts)
        num_instances = filter_properties.get('num_instances')
        var_matrix = variables.host_instance_matrix
        self.variables = [var_matrix[i][j] for i in range(num_hosts)
                                            for j in range(num_instances)]
        coeff_matrix = [[j + i for j in range(num_instances)]
                                                    for i in range(num_hosts)]
        self.coefficients = [coeff_matrix[i][j] for i in range(num_hosts)
                                                for j in range(num_instances)]


class FakeCostClass2(costs.BaseLinearCost):
    def _generate_components(self, variables, hosts, filter_properties):
        num_hosts = len(hosts)
        num_instances = filter_properties.get('num_instances')
        var_matrix = variables.host_instance_matrix
        self.variables = [var_matrix[i][j] for i in range(num_hosts)
                                            for j in range(num_instances)]
        coeff_matrix = [[i for j in range(num_instances)]
                                                    for i in range(num_hosts)]
        self.coefficients = [coeff_matrix[i][j] for i in range(num_hosts)
                                                for j in range(num_instances)]


class FakeConstraintClass1(constraints.BaseLinearConstraint):
    def _generate_components(self, variables, hosts, filter_properties):
        num_hosts = len(hosts)
        num_instances = filter_properties.get('num_instances')
        var_matrix = variables.host_instance_matrix
        for j in xrange(num_instances):
            self.variables.append([var_matrix[0][j]])
            self.coefficients.append([1])
            self.constants.append(0)
            self.operators.append('==')


class FakeConstraintClass2(constraints.BaseLinearConstraint):
    def _generate_components(self, variables, hosts, filter_properties):
        num_hosts = len(hosts)
        num_instances = filter_properties.get('num_instances')
        var_matrix = variables.host_instance_matrix
        for i in xrange(num_hosts):
            for j in xrange(num_instances):
                self.variables.append([var_matrix[i][j]])
                self.coefficients.append([1])
                self.constants.append(0)
                self.operators.append('==')


class FakeCostsFakeConstraintsTestCase(test.NoDBTestCase):
    def setUp(self):
        super(FakeCostsFakeConstraintsTestCase, self).setUp()
        self.fake_hosts = [host_manager.SolverSchedulerHostState(
                'fake_host%s' % x, 'fake-node') for x in xrange(1, 5)]
        self.fake_hosts += [host_manager.SolverSchedulerHostState(
                'fake_multihost', 'fake-node%s' % x) for x in xrange(1, 5)]

    def test_fake_costs(self):
        fake_variables = solvers.BaseVariables()
        fake_variables.host_instance_matrix = [
                ['h0i0', 'h0i1', 'h0i2'],
                ['h1i0', 'h1i1', 'h1i2'],
                ['h2i0', 'h2i1', 'h2i2'],
                ['h3i0', 'h3i1', 'h3i2']]
        fake_hosts = self.fake_hosts[0:4]
        fake_filter_properties = {'num_instances': 3}

        fake_cost_1 = FakeCostClass1()
        expected_cost_1_vars = [
                'h0i0', 'h0i1', 'h0i2', 'h1i0', 'h1i1', 'h1i2',
                'h2i0', 'h2i1', 'h2i2', 'h3i0', 'h3i1', 'h3i2']
        expected_cost_1_coeffs = [
                0.0, 1.0, 2.0, 1.0, 2.0, 3.0, 2.0, 3.0, 4.0, 3.0, 4.0, 5.0]
        cost_1_vars, cost_1_coeffs = fake_cost_1.get_components(
                        fake_variables, fake_hosts, fake_filter_properties)
        self.assertEqual(expected_cost_1_vars, cost_1_vars)
        self.assertEqual(expected_cost_1_coeffs, cost_1_coeffs)

        fake_cost_2 = FakeCostClass2()
        expected_cost_2_vars = [
                'h0i0', 'h0i1', 'h0i2', 'h1i0', 'h1i1', 'h1i2',
                'h2i0', 'h2i1', 'h2i2', 'h3i0', 'h3i1', 'h3i2']
        expected_cost_2_coeffs = [
                0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 3.0, 3.0, 3.0]
        cost_2_vars, cost_2_coeffs = fake_cost_2.get_components(
                        fake_variables, fake_hosts, fake_filter_properties)
        self.assertEqual(expected_cost_2_vars, cost_2_vars)
        self.assertEqual(expected_cost_2_coeffs, cost_2_coeffs)

    def test_fake_constraints(self):
        fake_variables = solvers.BaseVariables()
        fake_variables.host_instance_matrix = [
                ['h0i0', 'h0i1', 'h0i2'],
                ['h1i0', 'h1i1', 'h1i2'],
                ['h2i0', 'h2i1', 'h2i2'],
                ['h3i0', 'h3i1', 'h3i2']]
        fake_hosts = self.fake_hosts[0:4]
        fake_filter_properties = {'num_instances': 3}

        fake_constraint_1 = FakeConstraintClass1()
        expected_cons_1_vars = [['h0i0'], ['h0i1'], ['h0i2']]
        expected_cons_1_coeffs = [[1], [1], [1]]
        expected_cons_1_consts = [0, 0, 0]
        expected_cons_1_ops = ['==', '==', '==']
        cons_1_vars, cons_1_coeffs, cons_1_consts, cons_1_ops = (
                fake_constraint_1.get_components(
                        fake_variables, fake_hosts, fake_filter_properties))
        self.assertEqual(expected_cons_1_vars, cons_1_vars)
        self.assertEqual(expected_cons_1_coeffs, cons_1_coeffs)
        self.assertEqual(expected_cons_1_consts, cons_1_consts)
        self.assertEqual(expected_cons_1_ops, cons_1_ops)

        fake_constraint_2 = FakeConstraintClass2()
        expected_cons_2_vars = [
                ['h0i0'], ['h0i1'], ['h0i2'], ['h1i0'], ['h1i1'], ['h1i2'],
                ['h2i0'], ['h2i1'], ['h2i2'], ['h3i0'], ['h3i1'], ['h3i2']]
        expected_cons_2_coeffs = [[1] for i in range(12)]
        expected_cons_2_consts = [0 for i in range(12)]
        expected_cons_2_ops = ['==' for i in range(12)]
        cons_2_vars, cons_2_coeffs, cons_2_consts, cons_2_ops = (
                fake_constraint_2.get_components(
                        fake_variables, fake_hosts, fake_filter_properties))
        self.assertEqual(expected_cons_2_vars, cons_2_vars)
        self.assertEqual(expected_cons_2_coeffs, cons_2_coeffs)
        self.assertEqual(expected_cons_2_consts, cons_2_consts)
        self.assertEqual(expected_cons_2_ops, cons_2_ops)


class PulpSolverTestCase(test.NoDBTestCase):

    def setUp(self):
        super(PulpSolverTestCase, self).setUp()
        self.pulp_solver = pulp_solver.PulpSolver()
        self.fake_hosts = [host_manager.SolverSchedulerHostState(
                'fake_host%s' % x, 'fake-node') for x in xrange(1, 5)]
        self.fake_hosts += [host_manager.SolverSchedulerHostState(
                'fake_multihost', 'fake-node%s' % x) for x in xrange(1, 5)]

    def test_solve_one_cost_default_constraint(self):
        self.pulp_solver.cost_classes = [FakeCostClass1]
        self.pulp_solver.constraint_classes = [constraints.\
                non_trivial_solution_constraint.NonTrivialSolutionConstraint,
                constraints.valid_solution_constraint.ValidSolutionConstraint]

        hosts = self.fake_hosts[0:4]
        filter_properties = {
                'num_instances': 3,
                'instance_uuids': ['fake_uuid_%s' % x for x in range(3)],
                'request_spec': {}}

        with mock.patch.object(FakeCostClass1, 'cost_multiplier') as (
                                                    fake_cost_1_multiplier):
            fake_cost_1_multiplier.return_value = 1.0
            # FIXME: the comment below is not right, need normalization
            # resulting cost matrix will be:
            # [[0.0, 1.0, 2.0, 3.0],
            #  [1.0, 2.0, 3.0, 4.0],
            #  [2.0, 3.0, 4.0, 5.0],
            #  [3.0, 4.0, 5.0, 6.0]]
            expected_result = [
                    (hosts[0], 'fake_uuid_0'),
                    (hosts[0], 'fake_uuid_1'),
                    (hosts[1], 'fake_uuid_2')]
            result = self.pulp_solver.solve(hosts, filter_properties)
            self.assertEqual(set(expected_result), set(result))

    def test_solve_multi_costs_default_constraint(self):
        self.pulp_solver.cost_classes = [FakeCostClass1, FakeCostClass2]
        self.pulp_solver.constraint_classes = [constraints.\
                non_trivial_solution_constraint.NonTrivialSolutionConstraint,
                constraints.valid_solution_constraint.ValidSolutionConstraint]

        hosts = self.fake_hosts[0:4]
        filter_properties = {
                'num_instances': 4,
                'instance_uuids': ['fake_uuid_%s' % x for x in range(4)],
                'request_spec': {}}

        with contextlib.nested(
                mock.patch.object(FakeCostClass1, 'cost_multiplier'),
                mock.patch.object(FakeCostClass2, 'cost_multiplier')) as (
                fake_cost_1_multiplier, fake_cost_2_multiplier):
            fake_cost_1_multiplier.return_value = 1.0
            fake_cost_2_multiplier.return_value = (1.0)
            # resulting summed cost matrix will be:
            # [[0.0, 1.0, 2.0, 3.0],
            #  [2.0, 3.0, 4.0, 5.0],
            #  [4.0, 5.0, 6.0, 7.0],
            #  [6.0, 7.0, 8.0, 9.0]]
            expected_result = [
                    (hosts[0], 'fake_uuid_0'),
                    (hosts[0], 'fake_uuid_1'),
                    (hosts[0], 'fake_uuid_2'),
                    (hosts[1], 'fake_uuid_3')]
            result = self.pulp_solver.solve(hosts, filter_properties)
            self.assertEqual(set(expected_result), set(result))

    def test_solve_multi_costs_multi_constraints(self):
        self.pulp_solver.cost_classes = [FakeCostClass1, FakeCostClass2]
        self.pulp_solver.constraint_classes = [FakeConstraintClass1,
                constraints.non_trivial_solution_constraint.\
                NonTrivialSolutionConstraint,
                constraints.valid_solution_constraint.ValidSolutionConstraint]

        hosts = self.fake_hosts[0:4]
        filter_properties = {
                'num_instances': 4,
                'instance_uuids': ['fake_uuid_%s' % x for x in range(4)],
                'request_spec': {}}

        with contextlib.nested(
                mock.patch.object(FakeCostClass1, 'cost_multiplier'),
                mock.patch.object(FakeCostClass2, 'cost_multiplier')) as (
                fake_cost_1_multiplier, fake_cost_2_multiplier):
            fake_cost_1_multiplier.return_value = 1.0
            fake_cost_2_multiplier.return_value = (-0.5)
            # FIXME: the comment below is not right, need normalization
            # resulting summed cost matrix will be:
            # [[0.0, 1.0, 2.0, 3.0],
            #  [0.5, 1.5, 2.5, 3.5],
            #  [1.0, 2.0, 3.0, 4.0],
            #  [1.5, 2.5, 3.5, 4.5]]
            expected_result = [
                    (hosts[1], 'fake_uuid_0'),
                    (hosts[1], 'fake_uuid_1'),
                    (hosts[2], 'fake_uuid_2'),
                    (hosts[3], 'fake_uuid_3')]
            result = self.pulp_solver.solve(hosts, filter_properties)
            self.assertEqual(set(expected_result), set(result))

    def test_solve_multi_costs_multi_constraints_infeasible(self):
        self.pulp_solver.cost_classes = [FakeCostClass1, FakeCostClass2]
        self.pulp_solver.constraint_classes = [FakeConstraintClass1,
                FakeConstraintClass2, constraints.\
                non_trivial_solution_constraint.NonTrivialSolutionConstraint,
                constraints.valid_solution_constraint.ValidSolutionConstraint]

        hosts = self.fake_hosts[0:4]
        filter_properties = {
                'num_instances': 4,
                'instance_uuids': ['fake_uuid_%s' % x for x in range(4)],
                'request_spec': {}}

        with contextlib.nested(
                mock.patch.object(FakeCostClass1, 'cost_multiplier'),
                mock.patch.object(FakeCostClass2, 'cost_multiplier')) as (
                fake_cost_1_multiplier, fake_cost_2_multiplier):
            fake_cost_1_multiplier.return_value = 1.0
            fake_cost_2_multiplier.return_value = (-0.5)
            expected_result = []
            result = self.pulp_solver.solve(hosts, filter_properties)
            self.assertEqual(expected_result, result)
            #self.assertEqual(exception.SolverFailed,
            #        self.pulp_solver.solve, hosts, filter_properties)
