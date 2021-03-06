from __future__ import absolute_import
import pyrtl
from . import libutils


def main():
    print("You should be looking at the test case folder")


def kogge_stone(a, b, cin=0):
    """
    Creates a Kogge-Stone adder given two inputs

    :param a, b: The two Wirevectors to add up (bitwidths don't need to match)
    :param cin: An optimal carry Wirevector or value
    :return: a Wirevector representing the output of the adder

    The Kogge-Stone adder is a fast tree-based adder with O(log(n))
    propagation delay, useful for performance critical designs. However,
    it has O(n log(n)) area usage, and large fan out.
    """
    a, b = libutils.match_bitwidth(a, b)

    prop_orig = a ^ b
    prop_bits = [i for i in prop_orig]
    gen_bits = [i for i in a & b]
    prop_dist = 1

    # creation of the carry calculation
    while prop_dist < len(a):
        for i in reversed(range(prop_dist, len(a))):
            prop_old = prop_bits[i]
            gen_bits[i] = gen_bits[i] | (prop_old & gen_bits[i - prop_dist])
            if i >= prop_dist * 2:  # to prevent creating unnecessary nets and wires
                prop_bits[i] = prop_old & prop_bits[i - prop_dist]
        prop_dist *= 2

    # assembling the result of the addition
    # preparing the cin (and conveniently shifting the gen bits)
    gen_bits.insert(0, pyrtl.as_wires(cin))
    return pyrtl.concat(*reversed(gen_bits)) ^ prop_orig


def one_bit_add(a, b, cin):
    return pyrtl.concat(*_one_bit_add_no_concat(a, b, cin))


def _one_bit_add_no_concat(a, b, cin):
    assert len(a) == len(b) == len(cin) == 1
    sum = a ^ b ^ cin
    cout = a & b | a & cin | b & cin
    return cout, sum


def half_adder(a, b):
    assert len(a) == len(b) == 1
    sum = a ^ b
    cout = a & b
    return cout, sum


def ripple_add(a, b, cin=0):
    a, b = libutils.match_bitwidth(a, b)
    cin = pyrtl.as_wires(cin)
    if len(a) == 1:
        return one_bit_add(a, b, cin)
    else:
        ripplecarry = one_bit_add(a[0], b[0], cin)
        msbits = ripple_add(a[1:], b[1:], ripplecarry[1])
        return pyrtl.concat(msbits, ripplecarry[0])


def carrysave_adder(a, b, c, final_adder=ripple_add):
    """
    Adds three wirevectors up in an efficient manner
    :param a, b, c wirevector: the three wires to add up
    :param final_adder function: The adder to use to do the final addition
    :return: a wirevector with length 2 longer than the largest input
    """
    a, b, c = libutils.match_bitwidth(a, b, c)
    partial_sum = a ^ b ^ c
    shift_carry = (a | b) & (a | c) & (b | c)
    shift_carry_1 = pyrtl.concat(shift_carry, 0)
    return final_adder(partial_sum, shift_carry_1)


def cla_adder(a, b, cin=0, la_unit_len=4):
    """
    Carry Lookahead Adder
    :param int la_unit_len: the length of input that every unit processes

    A Carry LookAhead Adder is an adder that is faster than
    a ripple carry adder, as it calculates the carry bits faster.
    It is not as fast as a Kogge-Stone adder, but uses less area.
    """
    a, b = pyrtl.match_bitwidth(a, b)
    if len(a) <= la_unit_len:
        sum, cout = cla_adder_unit(a, b, cin)
        return pyrtl.concat(cout, sum)
    else:
        sum, cout = cla_adder_unit(a[0:la_unit_len], b[0:la_unit_len], cin)
        msbits = cla_adder(a[la_unit_len:], b[la_unit_len:], cout, la_unit_len)
        return pyrtl.concat(msbits, sum)


def cla_adder_unit(a, b, cin):
    """
    Carry generation and propogation signals will be calculated only using
    the inputs; their values don't rely on the sum.  Every unit generates
    a cout signal which is used as cin for the next unit.
    """
    gen = a & b
    prop = a ^ b
    assert(len(prop) == len(gen))

    carry = [gen[0] | prop[0] & cin]
    sum = prop[0] ^ cin

    cur_gen = gen[0]
    cur_prop = prop[0]
    for i in range(1, len(prop)):
        cur_gen = gen[i] | (prop[i] & cur_gen)
        cur_prop = cur_prop & prop[i]
        sum = pyrtl.concat(prop[i] ^ carry[i-1], sum)
        carry.append(gen[i] | (prop[i] & carry[i-1]))
    cout = cur_gen | (cur_prop & cin)
    return sum, cout


def wallace_reducer(wire_array_2, result_bitwidth, final_adder=kogge_stone):
    """
    The reduction and final adding part of a dada tree. Useful for adding many numbers together
    The use of single bitwidth wires is to allow for additional flexibility

    :param [[Wirevector]] wire_array_2: An array of arrays of single bitwidth
    wirevectors
    :param int result_bitwidth: The bitwidth you want for the resulting wire
    Used to eliminate unnessary wires
    :param final_adder: The adder used for the final addition
    :return: wirevector of length result_wirevector
    """
    return _general_adder_reducer(wire_array_2, result_bitwidth, True, final_adder)


def dada_reducer(wire_array_2, result_bitwidth, final_adder=kogge_stone):
    """
    The reduction and final adding part of a dada tree. Useful for adding many numbers together
    The use of single bitwidth wires is to allow for additional flexibility

    :param [[Wirevector]] wire_array_2: An array of arrays of single bitwidth
    wirevectors
    :param int result_bitwidth: The bitwidth you want for the resulting wire
    Used to eliminate unnessary wires
    :param final_adder: The adder used for the final addition
    :return: wirevector of length result_wirevector
    """
    return _general_adder_reducer(wire_array_2, result_bitwidth, False, final_adder)


def _general_adder_reducer(wire_array_2, result_bitwidth, reduce_2s, final_adder):
    """
    Does the reduction and final adding for bot dada and wallace recucers

    :param [[Wirevector]] wire_array_2: An array of arrays of single bitwidth
    wirevectors
    :param int result_bitwidth: The bitwidth you want for the resulting wire
    Used to eliminate unnessary wires
    :param Bool reduce_2s: True=Wallace Reducer, False=Dada Reducer
    :param final_adder: The adder used for the final addition
    :return: wirevector of length result_wirevector
    """
    # verification that the wires are actually wirevectors of length 1
    for wire_set in wire_array_2:
        for a_wire in wire_set:
            if not isinstance(a_wire, pyrtl.WireVector) or len(a_wire) != 1:
                raise pyrtl.PyrtlError(
                    "The item %s is not a valid element for the wire_array_2. "
                    "It must be a WireVector of bitwidth 1")

    while not all(len(i) <= 2 for i in wire_array_2):
        deferred = [[] for weight in range(result_bitwidth)]
        for i, w_array in enumerate(wire_array_2):  # Start with low weights and start reducing
            while len(w_array) >= 3:
                cout, sum = _one_bit_add_no_concat(*(w_array.pop(0) for j in range(3)))
                deferred[i].append(sum)
                if i + 1 < result_bitwidth:
                    deferred[i + 1].append(cout)

            if len(w_array) == 2 and reduce_2s:
                cout, sum = half_adder(*w_array)
                deferred[i].append(sum)
                if i + 1 < result_bitwidth:
                    deferred[i + 1].append(cout)
            else:
                deferred[i].extend(w_array)

        wire_array_2 = deferred

    # At this stage in the multiplication we have only 2 wire vectors left.
    # now we need to add them up
    result = _sparse_adder(wire_array_2, final_adder)
    if len(result) > result_bitwidth:
        return result[:result_bitwidth]
    else:
        return result


def _sparse_adder(wire_array_2, adder):
    bitwidth = len(wire_array_2)
    add_wires = [], []
    result = []
    for single_w_index in range(bitwidth):
        if len(wire_array_2[single_w_index]) == 2:  # Check if the two wire vectors overlap yet
            break
        result.append(wire_array_2[single_w_index][0])

    for w_loc in range(single_w_index, bitwidth):
        for i in range(2):
            if len(wire_array_2[w_loc]) >= i + 1:
                add_wires[i].insert(0, wire_array_2[w_loc][i])
            else:
                add_wires[i].insert(0, pyrtl.Const(0))

    adder_result = adder(pyrtl.concat(*add_wires[0]), pyrtl.concat(*add_wires[1]))
    return pyrtl.concat(adder_result, *reversed(result))

"""
Some adders that utilize these tree reducers
"""


def fast_group_adder(wires_to_add, reducer=wallace_reducer, final_adder=kogge_stone):
    """
    A generalization of the carry save adder, this is designed to add many numbers
    together in a both area and time efficient manner. Uses a tree reducer
    to achieve this performance


    :param [WireVector] wires_to_add: an array of wirevectors to add
    :param reducer: the tree reducer to use
    :param final_adder: The two value adder to use at the end
    :return: a wirevector with the result of the addition
      The length of the result is:
      max(len(w) for w in wires_to_add) + ceil(len(wires_to_add))
    """

    import math
    longest_wire_len = max(len(w) for w in wires_to_add)
    result_bitwidth = longest_wire_len + int(math.ceil(len(wires_to_add)))

    bits = [[] for i in range(longest_wire_len)]

    for wire in wires_to_add:
        for bit_loc, bit in enumerate(wire):
            bits[bit_loc].append(bit)

    return reducer(bits, result_bitwidth, final_adder)


if __name__ == "__main__":
    main()
