from __future__ import absolute_import
import pyrtl


def match_bitwidth(*args):
    # TODO: allow for custom bit extension functions
    """ Matches the bitwidth of all of the input arguments.
    :type args: WireVector
    :return tuple of args in order with extended bits
    """
    return pyrtl.match_bitwidth(*args)


def basic_n_bit_mux(ctrl, mux_in, default=None):

    default = pyrtl.Const(0) if default is None else default
    for ctrl_i in ctrl:
        next_mux_in = []
        for j in range((len(mux_in) + 1) // 2):
            second = default if 2*j + 1 >= len(mux_in) else mux_in[2*j + 1]
            next_mux_in.append(pyrtl.mux(select=ctrl_i,
                                         falsecase=mux_in[2*j], truecase=second))
        mux_in = next_mux_in
    return mux_in[0]


def variable_bit_matcher(select, mux_set):
    pass
    """ Matches up the select bit with a wire that matches up with first x bits.
    :param select: wirevector selecting the wire
    :param mux_set: a set storing matching (data, wirevector) pairs
    The value gives you the value returned by the mux on selection of the key
    Keys can be either (length (int), value (int)), or a const wirevector
    (remember to properly define length)
    :return:
    """
    # if first_match != "smallest" and first_match != "biggest":
    #     raise pyrtl.PyrtlError("The first match parameter for the variable bit matcher must be"
    #                            "either \"largest\" or \"smallest\" ")

    # convert const wirevectors for easier reading (and more data)
    mux_lst = []
    for i in mux_set:
        if isinstance(i[0], pyrtl.Const):
            mux_lst.append((len(i[0]), i[0], i[1]))
        else:
            mux_lst.append(i)
    filter_length = max(i[0] for i in mux_lst)

    # now convert to a dict for better filter performance
    mux_l_dict = [{} for i in range(filter_length + 1)]

    for i in mux_lst:
        # 0 element is the length, 1 element is the filter value,
        # and 2 element is the desired wirevector result
        mux_l_dict[i[0]][i[1]] = i[2]

    mux_result = [None for i in range(2**filter_length)]
    for cur_match_len in range(filter_length, 0, -1):
        new_m_result = []
        for new_w_index in range(2**(cur_match_len-1)):
            if new_w_index in mux_l_dict[cur_match_len]:
                pass
        mux_result = new_m_result


def partition_wire(wire, partition_size):
    if len(wire) % partition_size != 0:
        raise pyrtl.PyrtlError("Wire {} cannot be evenly partitioned into items of size {}"
                               .format(wire, partition_size))
    return [wire[offset:offset + partition_size] for offset in range(0, len(wire), partition_size)]


def str_to_int_array(string, base=16):
    """
    Converts a string to an array of integer values according to the
    base specified
    :return: [int]
    int numbers must be whitespace delimited
    Example:
    "13 a3 3c" => [0x13, 0xa3, 0x3c]
    """

    int_strings = string.split()
    return [int(int_str, base) for int_str in int_strings]
