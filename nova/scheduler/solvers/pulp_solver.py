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

from pulp import constants
from pulp import pulp

from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging
from nova.scheduler import solvers as scheduler_solver

LOG = logging.getLogger(__name__)


class PulpVariables(scheduler_solver.BaseVariables):
    
    def populate_variables(self, num_hosts, num_instances):
        self.host_instance_adjacency_matrix = [
                [pulp.LpVariable("HIA" + "_Host" + str(i) + "_Instance" +
                str(j), 0, 1, constants.LpInteger)
                for j in range(num_instances)] for i in range(num_hosts)]


class PulpSolver(scheduler_solver.BaseHostSolver):
    """A LP based pluggable LP solver implemented using PULP modeler."""

    variables_cls = PulpVariables

    def __init__(self):
        super(HostsPulpSolver, self).__init__()
        self.cost_classes = self._get_cost_classes()
        self.constraint_classes = self._get_constraint_classes()
        self.cost_weights = self._get_cost_weights()

    def solve(self, hosts, filter_properties):
        """This method returns a list of tuples - (host, instance_uuid)
        that are returned by the solver. Here the assumption is that
        all instance_uuids have the same requirement as specified in
        filter_properties.
        """
        host_instance_combinations = []

        num_instances = filter_properties['num_instances']
        num_hosts = len(hosts)

        instance_uuids = filter_properties.get('instance_uuids') or [
                '(unknown_uuid)' + str(i) for i in xrange(num_instances)]

        LOG.debug(_("All Hosts: %s") % [h.host for h in hosts])
        for host in hosts:
            LOG.debug(_("Host state: %s") % host)

        # Create dictionaries mapping temporary host/instance keys to
        # hosts/instance_uuids. These temorary keys are to be used in the
        # solving process since we need a convention of lp variable names.
        host_keys = ['Host' + str(i) for i in range(num_hosts)]
        host_key_map = dict(zip(host_keys, hosts))
        instance_keys = ['Instance' + str(i) for i in range(num_instances)]
        instance_key_map = dict(zip(instance_keys, instance_uuids))

        # Create the 'prob' variable to contain the problem data.
        prob = pulp.LpProblem("Host Instance Scheduler Problem",
                                constants.LpMinimize)

        # Create the 'variables' to contain the referenced variables.
        self.variables.populate_variables(num_hosts, num_instances)

        # Get costs and constraints and formulate the linear problem.
        self.cost_objects = [cost() for cost in self.cost_classes]
        self.constraint_objects = [constraint()
                for constraint in self.constraint_classes]

        cost_coefficients = []
        cost_variables = []
        for cost_object in self.cost_objects:
            weight = float(self.cost_weights[cost_object.__class__.__name__])
            current_coefficients = cost_object.get_coefficients(
                    self.variables, hosts, filter_properties)
            cost_coefficients.append([
                    weight * coeff for coeff in current_coefficients])
            cost_variables.append(cost_object.get_variables())
            #cost = cost_object.normalize_cost_matrix(cost, 0.0, 1.0)
            costs = [[costs[i][j] + weight * cost[i][j]
                    for j in range(num_instances)] for i in range(num_hosts)]
        LOG.debug(_("costs: %(costs)s") % {"costs": costs})
        prob += (pulp.lpSum([coeff * var
                for (coeff, var) in zip(cost_coefficients, cost_variables)]),
                "Sum_Costs")

        for constraint_object in self.constraint_objects:
            constraint_coefficients = constraint_object.get_coefficients(
                                    self.variables, hosts, filter_properties)
            LOG.debug(_("coeffs of %(name)s is: %(value)s") %
                        {"name": constraint_object.__class__.__name__,
                        "value": coefficient_vectors})
            constraint_constants = constraint_object.get_constants(
                                    self.variables, hosts, filter_properties)
            constraint_variables = constraint_object.get_variables(
                                    self.variables, hosts, filter_properties)
            constraint_operations = constraint_object.get_operations(
                                    self.variables, hosts, filter_properties)
            for i in range(len(operations)):
                operation = operations[i]
                len_variables = len(constraint_variables[i])
                prob += (
                        operation(pulp.lpSum(
                        [constraint_coefficients[i][j]
                        * constraint_variables[i][j]
                        for j in range(len_variables)]),
                        constraint_constants[i]),
                        "Costraint_Name_%s" %
                        constraint_object.__class__.__name__ + "_No._%s" % i)

        # The problem is solved using PULP's choice of Solver.
        prob.solve()

        # Create host-instance tuples from the solutions.
        if pulp.LpStatus[prob.status] == 'Optimal':
            for v in prob.variables():
                if v.name.startswith('HIA'):
                    (host_key, instance_key) = v.name.lstrip('HIA').lstrip(
                                                        '_').split('_')
                    if v.varValue == 1:
                        host_instance_combinations.append(
                                            (host_key_map[host_key],
                                            instance_key_map[instance_key]))
        else:
            LOG.warn(_("Pulp solver didnot find optimal solution! status: %s")
                    % pulp.LpStatus[prob.status])

        return host_instance_combinations
