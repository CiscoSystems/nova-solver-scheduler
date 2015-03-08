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
Constraints for scheduler constraint solvers
"""

from nova.compute import api as compute
from nova import loadables


class BaseConstraint(object):
    """Base class for constraints."""

    def get_components(self, variables, hosts, filter_properties):
        """Return the components of the constraint."""
        raise NotImplementedError()


class BaseLinearConstraint(BaseConstraint):
    """Base class of LP constraint."""

    def __init__(self):
        self.variables = []
        self.coefficients = []
        self.constants = []
        self.operations = []

    def _generate_components(self, variables, hosts, filter_properties):
        # override in a sub class
        pass

    def get_components(self, variables, hosts, filter_properties):
        self._generate_components(variables, hosts, filter_properties)
        return (self.variables, self.coefficients, self.constants,
                self.operations)


class AffinityConstraint(BaseConstraint):
    def __init__(self, *args, **kwargs):
        super(AffinityConstraint, self).__init__(*args, **kwargs)
        self.compute_api = compute.API()


class ConstraintHandler(loadables.BaseLoader):
    def __init__(self):
        super(ConstraintHandler, self).__init__(BaseLinearConstraint)


def all_constraints():
    """Return a list of constraint classes found in this directory.
    This method is used as the default for available constraints for
    scheduler and returns a list of all constraint classes available.
    """
    return ConstraintHandler().get_all_classes()
