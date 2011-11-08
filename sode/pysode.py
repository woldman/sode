# (c) Oscar Benjamin, 2011, under terms of the new BSD license
#
# Author: Oscar Benjamin
# Date: 08 Mar 2011
#
# This module defines the SODE class for numerical solution of Stochastic
# Ordinary Differential Equations with additive noise.

from __future__ import division

import re

import numpy as np


class SODESubclassError(NotImplementedError):
    """Exception raised by subclasses of SODE when the required subclass
    interface has not been defined"""
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class SODE(object):
    """The SODE class represents a set of Stochastic Ordinary Differential
    Equations. The SODEs take the form

        dXt = drift(Xt, t)dt + diffusion(Xt, t)dWt

    where X is a vector, drift and diffusion are vector fields and W is a
    vector of Wiener processes, and the equation is interpreted in the Ito
    sense.

    Subclasses should define the functions drift(x, t), diffusion(x, t),
    parameters and variables. drift and diffusion should accept both arguments
    (x, t) where t is scalar and x is a vector. drift and diffusion should
    return vectors of the same size as x.
    """

    # List of regexes that cannot be used for variable names or parameter
    # names. These are reserved because they cannot be used as attributes
    _RES = ['drift', 'diffusion', 'exact']
    _RES_BEG = ['set', 'get', 'load', 'save']
    _RE_RESERVED = [
        (r'^_.*$',
            "Names must not being with underscore: '{0}'"),
        (r'^({0})$'.format('|'.join(_RES)),
            "'{0}' is a reserved name"),
        (r'^({0})_.*$'.format('|'.join(_RES_BEG)),
            "Names ('{{0}}') cannot begin with {0}".format(','.join(_RES_BEG))),
    ]

    def __init__(self, **kwargs):
        """SODE(**kwargs)

        kwargs: dict specifying initial conditions and parameter values.

        Initial conditions should use variable name followed by '0'.
        Value must be understandable to the float() function.
        Parameters and initial conditions not supplied will have the default
        values from self.parameters and self.variables if not provided in
        kwargs.
        """
        # Check the appropriate variables are defined
        if not (hasattr(self, 'variables') and hasattr(self, 'parameters')):
            msg = "Subclasses should define parameters and variables"
            raise SODESubclassError(msg)

        # Check for reserved or duplicated parameter/variable names, establish
        # number of variables, and create x0
        self._init_pv(self.parameters, self.variables)

        # Read off parameter values specified in kwargs
        self._init_kwargs(**kwargs)

    #
    # The functions below define the SODE system. Since this is an abstract
    # class, we do not define them here.
    #

    # drift coefficient (deterministic derivative)
    def drift(self, a, x, t):
        raise SODESubclassError("Subclasses should override this function")

    # diffusion coefficient (noise amplitude)
    def diffusion(self, b, x, t):
        raise SODESubclassError("Subclasses should override this function")

    # exact solution (used in convergence calculations if provided
    def exact(self, x0, t, Wt):
        raise SODESubclassError("Subclasses should override this function")

    # Code for accessing variables:

    def _init_pv(self, parameters, variables):
        # Check for reserved or duplicated parameter/variable names
        vp_names = set()
        for name, _ in variables + parameters:
            for r, msg in self._RE_RESERVED:
                if re.match(r, name):
                    raise SODESubclassError(msg.format(name))
            if name in vp_names:
                raise ValueError("Duplicate name '{0}'".format(name))
            vp_names.add(name)

        # Prepare scene for variable/parameter access
        # _x0 is the array holding the initial conditions
        # Variable indices are stored as attributes with the same names
        self._variables = [var for var, _ in variables]
        self._parameters = [par for par, _ in parameters]
        self._x0 = np.zeros(len(self._variables))
        for n, var in enumerate(self._variables):
            self._set_var_index(var, n)
        # For convenience access later
        self.nvars = len(self._variables)

        # Initialise default values for parameters and variables
        for var, default in variables:
            self.set_ic(var, default)
        for par, default in parameters:
            self.set_parameter(par, default)

    def _init_kwargs(self, **kwargs):
        # Process parameters and ics provided in kwargs:
        for key, val in kwargs.iteritems():
            # Initial condition or parameter ?
            if key.endswith('0'):
                self.set_ic(key[:-1], val)
            else:
                try:
                    self.set_parameter(key, val)
                except ValueError:
                    pass

    def _shift_indices(self, offset, x0):
        # Copy old initial conditions and update indices
        for var in self._variables:
            old_index = self._get_var_index(var)
            new_index = old_index + offset
            x0[new_index] = self._x0[old_index]
            self._set_var_index(var, new_index)
        # Prevent this system from being used independently
        self._x0 = x0

    def get_variables(self):
        """Return a list of variable names"""
        return list(self._variables)

    def _varchk(self, var):
        if not var in self.get_variables():
            raise ValueError("No such variable {0}".format(var))

    def _get_var_index(self, var):
        return getattr(self, var)

    def _set_var_index(self, var, index):
        self._varchk(var)
        setattr(self, var, index)

    def get_ic(self, var):
        """Returns initial condition. Raises ValueError if unrecognised"""
        self._varchk(var)
        return self._x0[self._get_var_index(var)]

    def set_ic(self, var, val):
        """Set initial condition for var to float(val)"""
        self._varchk(var)
        self._x0[self._get_var_index(var)] = val

    def get_x0(self):
        """Return the initial condition as a vector suitable for drift and diffusion"""
        return self._x0.copy()

    # Code for accessing parameters

    def get_parameters(self):
        """Return a list of parameter names"""
        return list(self._parameters)

    def _parchk(self, par):
        if not par in self.get_parameters():
            raise ValueError("No such parameter {0}".format(par))

    def get_parameter(self, par):
        """Returns parameter value. Raises ValueError if unrecognised"""
        self._parchk(par)
        return getattr(self, par)

    def set_parameter(self, par, val):
        """Set parameter par to float(val)"""
        self._parchk(par)
        setattr(self, par, float(val))

    #
    # Pretty-print system
    #

    def get_description(self):
        """Print parameter values and initial condition to stdout"""
        lines = [self.__doc__]
        for name in self.get_parameters():
            lines.append('par {0} = {1}'.format(name, self.get_parameter(name)))
        for name in self.get_variables():
            lines.append('var {0} = {1}'.format(name, self.get_ic(name)))
        return '\n'.join(lines)

    #
    # Numerical routines
    #

class SODENetwork(SODE):
    """Specialises SODE for a system defined in terms of subsystems"""

    def __init__(self):
        """Initialise before adding subsystems"""
        # Empty subsystem data
        self._subsystems = [] # Remember order
        self._subsysdict = {} # Convenient access (want a sorteddict)

        # Initialise own parameters, variables with no kwargs
        super(SODENetwork, self).__init__()

    def init(self, **kwargs):
        """Flattens subsystems into single x0 and shifts indices"""

        # Determine indices of subsystems within larger state vector
        ntotal = self.nvars
        indices = []
        for name, sys in self._subsystems:
            indices.append((sys, ntotal))
            ntotal += sys.nvars

        # Create larger x0, and copy own values to the beginning
        x0 = np.zeros(ntotal)
        x0[:self.nvars] = self._x0
        self._x0 = x0
        self.nvars = ntotal

        # Now make all subsystems use a view into the larger array
        # Also copys subsystems values into the array
        for sys, n1 in indices:
            sys._shift_indices(n1, x0)

        # Compile list to be used in drift_subsys and diffusion_subsys
        # zero-d systems (just parameters) should be ignored for efficiency
        self._ss_eval = []
        for name, sys in self._subsystems:
            if sys.nvars:
                self._ss_eval.append(sys)

        # Now read off kwargs
        self._init_kwargs(**kwargs)

    # Add subsystem is called before __init__ so need to check everything here
    def add_subsystem(self, name, subsys):
        """Add a subsystem"""
        # Subsystem cannot be owned twice
        if hasattr(subsys, '_owned'):
            msg = "Cannot add already owned subsystem '{0}'".format(name)
            raise ValueError(msg)
        subsys._owned = self

        # Parameter access is non-unique if there are duplicate names
        if name in self._subsysdict:
            msg = "Duplicate subsystem name '{0}'".format(name)
            raise ValueError(msg)

        # Store subsystems and names
        self._subsystems.append((name, subsys))
        self._subsysdict[name] = subsys

    def _shift_indices(self, n, x0):
        # Shift child indices as well as own
        super(SODENetwork, self)._shift_indices(n, x0)
        for name, sys in self._subsystems:
            sys._shift_indices(n, x0)

    def get_parameters(self):
        # Retrieve own parameters
        pars = super(SODENetwork, self).get_parameters()
        # Retrieve subsystem parameters, with name prepended
        for name, sys in self._subsystems:
            for par in sys.get_parameters():
                pars.append('{0}.{1}'.format(name, par))
        return pars

    def get_variables(self):
        # Retrieve own parameters
        vars_ = super(SODENetwork, self).get_variables()
        # Retrieve subsystem parameters, with name prepended
        for name, sys in self._subsystems:
            for var in sys.get_variables():
                vars_.append('{0}.{1}'.format(name, var))
        return vars_

    # Use this to override get_/set_ par ic methods

    def _get_subsystem(self, pv_name):
        names = pv_name.split('.')
        snames, pv = names[:-1], names[-1]
        sys = self
        for sn in snames:
            if not hasattr(sys, '_subsysdict'):
                raise ValueError("No such subsystem '{0}'".format(sn))
            sys = sys._subsysdict[sn]
        return sys, pv

    def get_parameter(self, par):
        """Returns parameter value. Raises ValueError if unrecognised"""
        ss, par = self._get_subsystem(par)
        return SODE.get_parameter(ss, par)

    def set_parameter(self, par, val):
        """Set initial condition for var to float(val)"""
        ss, par = self._get_subsystem(par)
        return SODE.set_parameter(ss, par, val)

    def get_ic(self, var):
        """Returns initial condition. Raises ValueError if unrecognised"""
        ss, var = self._get_subsystem(var)
        return SODE.get_ic(ss, var)

    def set_ic(self, var, val):
        """Set initial condition for var to float(val)"""
        ss, var = self._get_subsystem(var)
        return SODE.set_ic(ss, var, val)

    # Subclasses must call these. They use self._ss_eval for efficiency

    def drift_subsys(self, a, x, t):
        """Compute drift for subsystems. Subclasses must call this in drift"""
        for sys in self._ss_eval:
            sys.drift(a, x, t)
        return a

    def diffusion_subsys(self, b, x, t):
        """Compute diffusion for subsystems. Subclasses must call this in
        diffusion"""
        for sys in self._ss_eval:
            sys.diffusion(b, x, t)
        return b


# Quick test suite to demonstrate usage of sode.py and script.py
if __name__ == "__main__":
    import doctest
    doctest.testmod()
