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
Metrics Cost.  Calculate hosts' costs by their metrics.

This can compute the costs based on the compute node hosts' various
metrics. The to-be computed metrics and their weighing ratio are specified
in the configuration file as the followings:

    [metrics]
    weight_setting = name1=1.0, name2=-1.0

    The final weight would be name1.value * 1.0 + name2.value * -1.0.
"""

from oslo.config import cfg

from nova.scheduler import utils
from nova.scheduler.solvers import costs as solver_costs

metrics_cost_opts = [
        cfg.FloatOpt('metrics_cost_multiplier',
                     default=(-1.0),
                     help='Multiplier used for metrics costs.'),
]

metrics_weight_opts = [
       cfg.FloatOpt('weight_multiplier_of_unavailable',
                     default=float(-1),
                     help='If any one of the metrics set by weight_setting '
                          'is unavailable, the metric weight of the host '
                          'will be set to (minw - (maxw - minw) * m), '
                          'where maxw and minw are the max and min weights '
                          'among all hosts, and m is the multiplier.'),
]

CONF = cfg.CONF
CONF.register_opts(metrics_cost_opts, group='solver_scheduler')
CONF.register_opts(metrics_weight_opts, group='metrics')
CONF.import_opt('weight_setting', 'nova.scheduler.weights.metrics',
                group='metrics')


class MetricsCost(solver_costs.BaseLinearCost):
    def __init__(self):
        self._parse_setting()

    def _parse_setting(self):
        self.setting = utils.parse_options(CONF.metrics.weight_setting,
                                           sep='=',
                                           converter=float,
                                           name="metrics.weight_setting")

    def cost_multiplier(self):
        return CONF.solver_scheduler.metrics_cost_multiplier

    def _generate_components(self, variables, hosts, filter_properties):
        num_hosts = len(hosts)
        num_instances = filter_properties.get('num_instances')

        host_weights = []
        numeric_values = []
        for host in hosts:
            metric_sum = 0.0
            for (name, ratio) in self.setting:
                metric = host.metrics.get(name, None)
                if metric:
                    metric_sum += metric.value * ratio
                else:
                    metric_sum = None
                    break
            host_weights.append(metric_sum)
            if metric_sum:
                numeric_values.append(metric_sum)
        if numeric_values:
            minval = min(numeric_values)
            maxval = min(numeric_values)
            weight_of_unavailable = (minval - (maxval - min_val) *
                                CONF.metrics.weight_multiplier_of_unavailable)
            for i in range(num_hosts):
                if host_weights is None:
                    host_weights = weight_of_unavailable
        else:
            host_weights[i] = 0 for i in range(num_hosts)

        var_matrix = variables.host_instance_adjacency_matrix
        self.variables = [var_matrix[i][j] for i in range(num_hosts)
                                                for j in range(num_instances)]

        coeff_matrix = [[host_weights[i] for j in range(num_instances)]
                                                    for i in range(num_hosts)]
        self.coefficients = [coeff_matrix[i][j] for i in range(num_hosts)
                                                for j in range(num_instances)]
