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
Scheduler host constraint solvers
"""

from oslo.config import cfg

from nova.scheduler.solvers import costs
from nova.scheduler.solvers import constraints

scheduler_solver_opts =[
        cfg.ListOpt('scheduler_solver_costs',
                    default=['RamCost'],
                    help='Which cost matrices to use in the '
                         'scheduler solver.'),
        cfg.ListOpt('scheduler_solver_constraints',
                    default=['ActiveHostsConstraint',
                            'NonTrivialSolutionConstraint',
                            'ValidSolutionConstraint'],
                    help='Which constraints to use in scheduler solver'),
]

CONF = cfg.CONF
CONF.register_opts(scheduler_solver_opts, group='solver_scheduler')


class BaseVariables(object):
    """Defines the convention of variables to be used in solvers.
    The variables are supposed to be passed to costs/constraints where they
    will be reorganized to form optimization problems."""
    def __init__(self):
        self.host_instance_matrix = []

    def populate_variables(self, *args, **kwargs):
        raise NotImplementedError


class BaseHostSolver(object):
    """Base class for host constraint solvers."""

    # Overwrite in sub-class
    variables_cls = BaseVariables

    def __init__(self):
        self.variables = self.variables_cls()

    def _get_cost_classes(self):
        """Get cost classes from configuration."""
        cost_classes = []
        cost_handler = costs.CostHandler()
        all_cost_classes = cost_handler.get_all_classes()
        expected_costs = CONF.solver_scheduler.scheduler_solver_costs
        for cost in all_cost_classes:
            if cost.__name__ in expected_costs:
                cost_classes.append(cost)
        return cost_classes

    def _get_constraint_classes(self):
        """Get constraint classes from configuration."""
        constraint_classes = []
        constraint_handler = constraints.ConstraintHandler()
        all_constraint_classes = constraint_handler.get_all_classes()
        expected_constraints = (
                CONF.solver_scheduler.scheduler_solver_constraints)
        for constraint in all_constraint_classes:
            if constraint.__name__ in expected_constraints:
                constraint_classes.append(constraint)
        return constraint_classes

    def solve(self, hosts, filter_properties):
        """Return the list of host-instance tuples after
           solving the constraints.
           Implement this in a subclass.
        """
        raise NotImplementedError()
