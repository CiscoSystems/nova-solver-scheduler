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

"""
Tests for solver scheduler constraints.
"""

from nova import context
from nova.scheduler.solvers import constraints
from nova import test
from nova.tests.scheduler import solver_scheduler_fakes as fakes


class ConstraintTestBase(test.NoDBTestCase):
    """Base test case for constraints."""
    def setUp(self):
        super(ConstraintTestBase, self).setUp()
        self.context = context.RequestContext('fake', 'fake')
        constraint_handler = constraints.ConstraintHandler()
        classes = constraint_handler.get_matching_classes(
                    ['nova.scheduler.solvers.constraints.all_constraints'])
        self.class_map = {}
        for c in classes:
            self.class_map[c.__name__] = c


class ConstraintsTestCase(ConstraintTestBase):
    def test_all_constraints(self):
        """Test the existence of all constraint classes."""
        self.assertIn('NoLinearConstraint', self.class_map)
        self.assertIn('NonTrivialSolutionConstraint', self.class_map)
        self.assertIn('ActiveHostsConstraint', self.class_map)
        self.assertIn('DifferentHostConstraint', self.class_map)

    def test_base_linear_constraints(self):
        blc = constraints.BaseLinearConstraint()
        variables, coefficients, constants, operators = (
                                        blc.get_components(None, None, None))
        self.assertEqual([], variables)
        self.assertEqual([], coefficients)
        self.assertEqual([], constants)
        self.assertEqual([], operators)
