import pyrtl
import random

__author__ = 'John Clow'

"""
testcase_utils

This file (intentionally misspelled) is created to store common utility
functions used for the test cases.

I am documenting this rather well because users have
a good reason to look at it - John Clow
"""


def make_wires_and_values(num_wires, max_bitwidth=None, exact_bitwidth=None):
    """
    Generates multiple input wires and sets of test values for
    testing purposes
    :return: wires, lists of values for the wires
    """
    min_bitwidth, max_bitwidth = calcuate_max_and_min_bitwidths(max_bitwidth, exact_bitwidth)
    wires, vals = list(zip(*(
        generate_in_wire_and_values(random.randrange(min_bitwidth, max_bitwidth + 1))
        for i in range(num_wires))))
    return wires, vals


def calcuate_max_and_min_bitwidths(max_bitwidth=None, exact_bitwidth=None):
    if max_bitwidth is not None:
        min_bitwidth = 1
    elif exact_bitwidth is not None:
        min_bitwidth = max_bitwidth = exact_bitwidth
    else:
        raise pyrtl.PyrtlError("A max or exact bitwidth must be specified")
    return min_bitwidth, max_bitwidth


def generate_in_wire_and_values(bitwidth, num_test_vals=20, name=None):
    """
    Generates an input wire and a set of test values for
    testing purposes
    :param bitwidth: The bitwidth of the value you wish to generate
    :return: tuple consisting of input_wire, test_vaues
    """
    input_wire = pyrtl.Input(bitwidth, name=name)  # Creating a new input wire
    test_vals = [_random_test_value(bitwidth) for i in range(num_test_vals)]
    return input_wire, test_vals


def _random_test_value(bitwidth):
    # Note that this is not uniformly distributed
    return int(2**random.uniform(0, bitwidth)-1)


def make_consts(num_wires, max_bitwidth=None, exact_bitwidth=None):
    """
    returns [Const] [Const vals]
    """
    min_bitwidth, max_bitwidth = calcuate_max_and_min_bitwidths(max_bitwidth, exact_bitwidth)
    bitwidths = [random.randrange(min_bitwidth, max_bitwidth + 1) for i in range(num_wires)]
    wires = [pyrtl.Const(_random_test_value(b), b) for b in bitwidths]
    vals = [w.val for w in wires]
    return wires, vals


def sim_and_ret_out(outwire, inwires, invals):
    """
    Simulates the net using the inwires, invalues and returns the output array
    Used for rapid test development

    :param outwire: The wire to return the output of
    :param [Input, ...] inwires: a list of wires to read in from
    :param [[int, ...], ...] invals: a list of input value lists
    :return: a list of values from the output wire simulation result
    """
    sim_trace = pyrtl.SimulationTrace()  # Creating a logger for the simulator
    sim = pyrtl.Simulation(tracer=sim_trace)  # Creating the simulation
    for cycle in range(len(invals[0])):
        # for each call to step(), we supply a dictionary of wires to their
        # corresponding value for the cycle (The simulator then simulates it)
        sim.step({wire: val[cycle] for wire, val in zip(inwires, invals)})

    return sim_trace.trace[outwire]  # Pulling the value of outwire straight from the log
