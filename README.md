Openstack Nova Solver Scheduler
===============================

Solver Scheduler is an Openstack Nova Scheduler driver that provides a smarter, complex constraints optimization based resource scheduling in Nova.  It is a pluggable scheduler driver, that can leverage existing complex constraint solvers available in open source such as PULP, CVXOPT, Google OR-TOOLS, etc. It can be easily extended to add complex constraint models for various use cases, written using any of the available open source constraint solving frameworks. 

Requirements
------------

* pulp>=1.4.6

Installation
------------

In the current stage, we provide a manual way to install the solver-scheduler code to existing nova directory. In this section, we will also guide you through installing the solver scheduler with the minimum configuration. For instructions of configuring a fully functional solver-scheduler, please check out the next sections.  
Please make sure that you have nova Icehouse already installed on the machine.  


* **Prerequisites**  
    - install the python package: pulp >= 1.4.6  
      ```
      pip install pulp
      ```  

* **Manual Installation**  

    - Clone the repository to your local host where nova-scheduler is run, and switch to the "dev-mvp1" branch.    
      ```
      git clone https://github.com/CiscoSystems/nova-solver-scheduler.git
      git checkout -b dev-mvp1 origin/dev-mvp1
      ```

    - Navigate to the local repository and copy the contents in 'nova' sub-directory to the corresponding places in existing nova.  
      ```
      cp -r nova-solver-scheduler/nova $NOVA_PARENT_DIR
      ```  
      (replace the $NOVA_PARENT_DIR with actual directory name. eg. /usr/local/lib/python2.7/site-packages/)  
      This will add solver-scheduler codes to existing nova directory. The files in nova-solver-scheduler/nova do not overlap with existing nova files, therefore nothing should be overridden. We list below the files and directories which will be copied, just in case you want to double check.

    - Update the nova configuration file (e.g. /etc/nova/nova.conf) with the minimum option below. If the option already exists, modify its value, otherwise add it to the config file. Check the "Configurations" section below for a full configuration guide.  
      ```
      [DEFAULT]
      ...
      scheduler_driver=nova.scheduler.solver_scheduler.ConstraintSolverScheduler  
      scheduler_host_manager=nova.scheduler.host_manager.SolverSchedulerHostManager
      ```  

    - Restart the nova scheduler.  
      ```service nova-scheduler restart```  

    - Done. The nova-solver-scheduler should be working with a demo configuration.  

* **Uninstallation**  

    - If you need to switch to other scheduler, simply open the nova configuration file and edit the option ```scheduler_driver``` and ```scheduler_host_manager```, then restart nova-scheduler.  e.g., 
    ```
    scheduler_driver=nova.scheduler.filter_scheduler.FilterScheduler
    scheduler_host_manager=nova.scheduler.host_manager.HostManager
    ```  

    - To remove all codes of solver-scheduler, manually delete the files/directories listed below from the nova directory.  

    - Please remember to restart the nova-scheduler service everytime when changes are made in the code or config file.  

* **List of installed files**  

    nova/scheduler/solvers (directory)  
    nova/scheduler/solver_scheduler.py  
    nova/scheduler/solver_scheduler_host_manager.py  
    nova/tests/scheduler/solvers (directory)  
    nova/tests/scheduler/solver_scheduler_fakes.py  
    nova/tests/scheduler/test_solver_scheduler.py  
    nova/tests/scheduler/test_solver_scheduler_host_manager.py  
    nova/solver_scheduler_exception.py  

Configurations
--------------

* This is a (default) configuration sample for the solver-scheduler. Please add/modify these options in /etc/nova/nova.conf.
* Note:
    - Please carefully make sure that options in the configuration file are not duplicated. If an option name already exists, modify its value instead of adding a new one of the same name.
    - Please refer to the 'Configuration Details' section below for proper configuration and usage of costs and constraints.

```
[DEFAULT]

...

#
# Options defined in nova.scheduler.manager
#

# Default driver to use for the scheduler (string value)
scheduler_driver=nova.scheduler.solver_scheduler.ConstraintSolverScheduler

#
# Options defined in nova.scheduler.driver
#

# The scheduler host manager class to use (string value)
scheduler_host_manager=nova.scheduler.host_manager.SolverSchedulerHostManager

#
# Options defined in nova.scheduler.filters.core_filter
#

# Virtual CPU to physical CPU allocation ratio which affects
# all CPU filters. This configuration specifies a global ratio
# for CoreFilter. For AggregateCoreFilter, it will fall back
# to this configuration value if no per-aggregate setting
# found. This option is also used in Solver Scheduler for the
# MaxVcpuAllocationPerHostConstraint  (floating point value)
cpu_allocation_ratio=16.0

#
# Options defined in nova.scheduler.filters.disk_filter
#

# Virtual disk to physical disk allocation ratio (floating
# point value)
disk_allocation_ratio=1.0

#
# Options defined in nova.scheduler.filters.num_instances_filter
#

# Ignore hosts that have too many instances (integer value)
max_instances_per_host=50

#
# Options defined in nova.scheduler.filters.ram_filter
#

# Virtual ram to physical ram allocation ratio which affects
# all ram filters. This configuration specifies a global ratio
# for RamFilter. For AggregateRamFilter, it will fall back to
# this configuration value if no per-aggregate setting found.
# (floating point value)
ram_allocation_ratio=1.5

#
# Options defined in nova.scheduler.filters.io_ops_filter
#

# Ignore hosts that have too many
# builds/resizes/snaps/migrations. (integer value)
max_io_ops_per_host=8

#
# Options defined in nova.scheduler.weights.ram
#

# Multiplier used for weighing ram.  Negative numbers mean to
# stack vs spread. (floating point value)
ram_weight_multiplier=1.0


[solver_scheduler]

#
# Options defined in nova.scheduler.solver_scheduler
#

# The pluggable solver implementation to use. By default, a
# reference solver implementation is included that models the
# problem as a Linear Programming (LP) problem using PULP.
# (string value)
scheduler_host_solver=nova.scheduler.solvers.pulp_solver.PulpSolver

# This fallback scheduler will be used automatically if the
# solver scheduler fails to get a solution. (string value)
fallback_scheduler=nova.scheduler.filter_scheduler.FilterScheduler

# Whether to use a fallback scheduler in case the solver
# scheduler fails to get a solution because of a solver
# failure. (boolean value)
enable_fallback_scheduler=true


#
# Options defined in nova.scheduler.solvers
#

# Which cost matrices to use in the scheduler solver. (list
# value)
scheduler_solver_costs=RamCost

# Which constraints to use in scheduler solver (list value)
scheduler_solver_constraints=ActiveHostsConstraint,NonTrivialSolutionConstraint,ValidSolutionConstraint


#
# Options defined in nova.scheduler.solvers.costs.metrics_cost
#

# Multiplier used for metrics costs. (floating point value)
metrics_cost_multiplier=1.0


#
# Options defined in nova.scheduler.solvers.costs.ram_cost
#

# Multiplier used for ram costs. Negative numbers mean to
# stack vs spread. (floating point value)
ram_cost_multiplier=1.0


#
# Options defined in nova.scheduler.solvers.pulp_solver
#

# How much time in seconds is allowed for solvers to solve the
# scheduling problem. If this time limit is exceeded the
# solver will be stopped. (integer value)
pulp_solver_timeout_seconds=20


[metrics]

#
# Options defined in nova.scheduler.solvers.costs.metrics_cost
#

# If any one of the metrics set by weight_setting is
# unavailable, the metric weight of the host will be set to
# (minw + (maxw - minw) * m), where maxw and minw are the max
# and min weights among all hosts, and m is the multiplier.
# (floating point value)
weight_multiplier_of_unavailable=-1.0

...

```

Configuration Details
---------------------

Here we list a few constraints that can be configured, we will update this part and add more details soon.  
To enable them, edit the configuration option 'scheduler_solver_constraints' under the '[solver_scheduler]' section of the nova configuration file.  

* **Constraint options**  

    - **ActiveHostConstraint**  
        By enabling this constraint, only enabled and operational hosts are allowed to be selected.  
        Normally this constraint should always be enabled.  
    
    - **NonTrivialSolutionConstraint**  
        The purpose of this constraint is to avoid trivial solution (i.e. instances placed nowhere).  
        This constraint must always be enabled to ensure solution is meaningful.  

    - **ValidSolutionConstraint**  
        This makes sure that the solution generated by solver scheduler is valid to its mathematic formulations.  
        This constraint must always be enabled to ensure solution is valid.  
    
    - **RamConstraint**  
        Cap the virtual ram allocation of hosts.  
        The following option should be set in the '[DEFAULT]' section of nova configuration file if this constraint is used:  
        ```ram_allocation_ratio=<a positive real number>``` (virtual-to-physical ram allocation ratio, if >1.0 then over-allocation is allowed.)  
    
    - **DiskConstraint**  
        Cap the virtual disk allocation of hosts.  
        The following option should be set in the '[DEFAULT]' section of nova configuration file if this constraint is used:  
        ```disk_allocation_ratio=<a positive real number>``` (virtual-to-physical disk allocation ratio, if >1.0 then over-allocation is allowed.)  
    
    - **VcpuConstraint**  
        Cap the vcpu allocation of hosts.  
        The following option should be set in the '[DEFAULT]' section of nova configuration file if this constraint is used:  
        ```cpu_allocation_ratio=<a positive real number>``` (virtual-to-physical cpu allocation ratio, if >1.0 then over-allocation is allowed.)  
    
    - **NumInstancesPerHostConstraint**  
        Specify the maximum number of instances that can be placed in each host.  
        The following option should be set in the '[DEFAULT]' section of nova configuration file if this constraint is used:  
        ```max_instances_per_host=<a positive integer>```  
    
    - **DifferentHostConstraint**  
        Force instances to be placed at different hosts as specified instance(s).  
        The following scheduler hint is expected in the server booting command when using this constraint:  
        ```different_host=<a (list of) instance uuid(s)>```  
    
    - **SameHostConstraint**  
        Force instances to be placed at same hosts as specified instance(s).  
        The following scheduler hint is expected in the server booting command when using this constraint:  
        ```same_host=<a (list) of instance uuid(s)>```  

    - **ServerGroupAffinityConstraint**  
        To use this constraint, you must first have a server group with policy 'affinity' specified. The scheduler will make sure all servers in the group are scheduled in a same host.  
        The following scheduler hint is expected in the server booting command when using this constraint:  
        ```group=<uuid of the server group this new server will belong to>```  

    - **ServerGroupAntiAffinityConstraint**  
        To use this constraint, you must first have a server group with polity 'anti-affinity' specified. The scheduler will make sure all servers in the group are scheduled in different hosts.  
        The following scheduler hint is expected in the server booting command when using this constraint:  
        ```group=<uuid of the server group this new server belongs to>```  

    TBD......
