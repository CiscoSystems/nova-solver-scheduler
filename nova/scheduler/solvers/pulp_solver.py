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

from oslo.config import cfg

from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging
from nova.scheduler import solvers as scheduler_solver
from nova import weights

pulp_solver_opts =[
        cfg.IntOpt('pulp_solver_timeout_seconds',
                    default=20,
                    help='How much time in seconds is allowed for solvers to '
                         'solve the scheduling problem. If this time limit '
                         'is exceeded the solver will be stopped.'),
]

CONF = cfg.CONF
CONF.register_opts(pulp_solver_opts, group='solver_scheduler')

LOG = logging.getLogger(__name__)


class PulpVariables(scheduler_solver.BaseVariables):
    
    def populate_variables(self, host_keys, instance_keys):
        self.host_instance_matrix = [
                [pulp.LpVariable("HIA_" + host_key + instance_key, 0, 1,
                constants.LpInteger) for instance_key in instance_keys]
                for host_key in host_keys]


class PulpSolver(scheduler_solver.BaseHostSolver):
    """A LP based pluggable LP solver implemented using PULP modeler."""

    variables_cls = PulpVariables

    def __init__(self):
        super(HostsPulpSolver, self).__init__()
        self.cost_classes = self._get_cost_classes()
        self.constraint_classes = self._get_constraint_classes()

    def _get_operation(self, op_str):
        ops = {
                '==': lambda x, y: x == y,
                '!=': lambda x, y: x != y,
                '>=': lambda x, y: x >= y,
                '<=': lambda x, y: x <= y,
                '>': lambda x, y: x > y,
                '<': lambda x, y: x < y}
        return ops.get(op_str)

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

        # Create the 'variables' to contain the referenced variables.
        self.variables.populate_variables(host_keys, instance_keys)

        # Create the 'prob' variable to contain the problem data.
        prob = pulp.LpProblem("Host Instance Scheduler Problem",
                                constants.LpMinimize)

        # Get costs and constraints and formulate the linear problem.

        # Add costs.
        cost_objects = [cost() for cost in self.cost_classes]
        cost_coefficients = []
        cost_variables = []
        for cost_object in self.cost_objects:
            var_list, coeff_list = cost_object.get_components(
                                    self.variables, hosts, filter_properties)
            cost_variables.append(var_list)
            normalized_costs = list(weights.normalize(coeff_list))
            cost_coefficients.append([val * cost_object.cost_multiplier
                                                for val in normalized_costs])
            LOG.debug(_("cost coeffs of %(name)s is: %(value)s") %
                    {"name": cost_object.__class__.__name__,
                    "value": coeff_list})
        if cost_variables:
            prob += (pulp.lpSum([cost_coefficients[i] * cost_variables[i]
                    for i in range(len(cost_variables))]), "Sum_Costs")

        # Add constraints.
        constraint_objects = [constraint()
                                for constraint in self.constraint_classes]
        for constraint_object in self.constraint_objects:
            vars_list, coeffs_list, consts_list, ops_list = (
                    constraint_object.get_components(self.variables, hosts,
                    filter_properties))
            LOG.debug(_("coeffs of %(name)s is: %(value)s") %
                    {"name": constraint_object.__class__.__name__,
                    "value": coefficient_vectors})
            for i in range(len(ops_list)):
                operation = self._get_operation(ops_list[i])
                prob += (
                        operation(pulp.lpSum([coeffs_list[i][j] *
                        vars_list[i][j] for j in range(len(vars_list))]),
                        consts_list[i]), "Costraint_Name_%s" %
                        constraint_object.__class__.__name__ + "_No._%s" % i)

        # The problem is solved using PULP's choice of Solver.
        prob.solve(pulp.solvers.PULP_CBC_CMD(
                maxSeconds=CONF.solver_scheduler.pulp_solver_timeout_seconds))

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
