#

# See the end of the file for the __all__ definition.

def memoize(function):
    memo = {}
    def wrapper(*args):
        if args in memo:
            return memo[args]
        rv = function(*args)
        memo[args] = rv
        return rv
    return wrapper

## Instruction definition and parsing.

II_MASK = 0
II_NAME = 1
II_FLAGS = 2
II_TEXT = 3
II_ANDMASK = 4
II_CMPMASK = 5
II_EXTRAWORDS = 6
II_SRCEAMASK = 7
II_DSTEAMASK = 8
II_LENGTH = 9

def make_operand_mask(mask_string):
    and_mask = cmp_mask = 0
    for c in mask_string:
        and_mask <<= 1
        cmp_mask <<= 1
        if c == '0':
            and_mask |= 1
        elif c == '1':
            and_mask |= 1
            cmp_mask |= 1
    return and_mask, cmp_mask


class Specification(object):
    key = None
    mask_char_vars = None
    filter_keys = None
    ea_args = None


@memoize
def _make_specification(format):
    @memoize
    def get_substitution_vars(s):
        d = {}
        for candidate_string in s[1:-1].split("&"):
            k, v = [ t.strip() for t in candidate_string.split("=") ]
            d[k] = v
        return d

    # TYPE:CHAR
    # TYPE:CHAR(TYPE FILTER OPTION|...)
    # TYPE:VARLIST[FILTER_OPTION|...]
    spec = Specification()
    spec.mask_char_vars = {}

    idx_typeN = format.find(":")
    if idx_typeN == -1:
        spec.key = format
        return spec
    spec.key = format[:idx_typeN].strip()

    idx_charvarsN = len(format)
    idx_filter0 = format.find("{")
    if idx_filter0 != -1:
        idx_filterN = format.find("}", idx_filter0)
        spec.filter_keys = [ s.strip() for s in format[idx_filter0+1:idx_filterN].split("|") ]
        idx_charvarsN = idx_filter0-1

    idx_charvars0 = format.find("(", idx_typeN+1)
    if idx_charvars0 != -1:
        charvar_string = format[idx_charvars0:idx_charvarsN+1]
        spec.mask_char_vars = get_substitution_vars(charvar_string)

    return spec


def process_instruction_list(_A, _list):
    # Pass 1: Each instruction entry with a ".z" size wildcard are expanded to specific entries.
    #         e.g. INSTR.z OP, OP -> INSTR.w OP, OP / INSTR.l OP, OP / ...
    _list_old = _list
    _list = []
    while len(_list_old):
        entry = _list_old.pop()
        if " " in entry[II_NAME]:
            # <INSTR>(\.z)? <OPERAND>, ..
            entry_name, operands_string = entry[II_NAME].split(" ", 1)
            operands_string = " "+ operands_string.strip()
        else:
            # <INSTR>(\.z)?
            entry_name = entry[II_NAME]
            operands_string = ""

        # Size-based processing.
        specification = _make_specification(entry_name)
        if "z" in specification.mask_char_vars:
            mask_char_vars = specification.mask_char_vars.copy()
            del mask_char_vars["z"]

            # Append a new substitution mapping without the 'z' entry.
            new_name = specification.key
            var_list = mask_char_vars.items()
            if len(var_list):
                new_name += ":(" + "&".join(k+"="+v for (k, v) in var_list) +")"

            for size_entry in _A.create_duplicated_instruction_entries(entry, new_name, operands_string):
                _list.append(size_entry)
        else:
            _list.append(entry)

    # Pass 2: Sort all entries by known bits to reduce hitting matches with unknown bits first.
    #         Also inject calculated columns.
    d = {}
    for entry in _list:
        operand_mask = entry[II_MASK]

        # Ensure pre-calculated columns have space present and precalculate some useful information.
        entry.extend([ None ] * (II_LENGTH - len(entry)))

        # Matching and comparison masks.
        and_mask, cmp_mask = make_operand_mask(operand_mask)
        entry[II_ANDMASK] = and_mask
        entry[II_CMPMASK] = cmp_mask

        # Extra word needs.
        max_extra_words = 0
        line_bits = entry[II_NAME].split(" ", 1)
        if len(line_bits) > 1:
            operands_bits = line_bits[1].split(",")
            for operand_string in operands_bits:
                spec = _make_specification(operand_string)
                for var_name, value_name in spec.mask_char_vars.iteritems():
                    if value_name[0] == "I":
                        size_idx = value_name.find(".")
                        if size_idx > 0:
                            word_idx = int(value_name[1:size_idx])
                            extra_words = word_idx
                            size_char = value_name[size_idx+1]
                            # B (extracted from given word), W (extracted from given word), L (requires extra word)
                            if size_char == "L":
                                extra_words += 1
                            if extra_words > max_extra_words:
                                max_extra_words = extra_words
        entry[II_EXTRAWORDS] = max_extra_words

        # Operand type mask generation.
        name_bits = entry[II_NAME].split(" ", 1)
        if len(name_bits) > 1:
            for i, operand_string in enumerate(name_bits[1].split(",")):
                mask = 0
                spec = _make_specification(operand_string)
                if spec.filter_keys is not None:
                    for ea_key in spec.filter_keys:
                        mask |= 1 << get_EAM_id(ea_key)
                if i == 0:
                    entry[II_SRCEAMASK] = mask
                elif i == 1:
                    entry[II_DSTEAMASK] = mask

        # Sort..
        sort_key = ""
        sort_idx = 0
        for i, c in enumerate(operand_mask):
            if c == '0' or c == '1':
                sort_key += c
            else:
                if sort_idx == 0: sort_idx = len(operand_mask) - i
                sort_key += '_'
        if (sort_idx, sort_key) in d:
            print "Duplicate (first):", d[(sort_idx, sort_key)]
            print "Duplicate (second):", entry
            raise RuntimeError("duplicate mask", sort_idx, sort_key)
        d[(sort_idx, sort_key)] = entry

    ls = d.keys()
    ls.sort()
    _list = [ d[k] for k in ls ]
    
    return _list


## Architecture interface.

def _unimplemented_function(*args, **kwargs): raise NotImplementedError("arch-function-undefined")


class ArchInterface(object):
    """ This object allows an interface to define functionality implementations, and default constants. """

    """ Constant: Prefix for immediate values. """
    constant_immediate_prefix = ""
    """ Constant: Prefix for binary values. """
    constant_binary_prefix = "arch-constant-undefined"
    """ Constant: Suffix for binary values. """
    constant_binary_suffix = "arch-constant-undefined"
    """ Constant: Prefix for decimal values. """
    constant_decimal_prefix = "arch-constant-undefined"
    """ Constant: Suffix for decimal values. """
    constant_decimal_suffix = "arch-constant-undefined"
    """ Constant: Prefix for hexadecimal values. """
    constant_hexadecimal_prefix = "arch-constant-undefined"
    """ Constant: Suffix for hexadecimal values. """
    constant_hexadecimal_suffix = "arch-constant-undefined"
    """ Constant: Core architecture bit mask. """
    constant_core_architecture_mask = 0

    """ Function: Identify if the given instruction alters the program counter. """
    function_is_final_instruction = _unimplemented_function
    """ Function: . """
    function_get_match_addresses = _unimplemented_function
    """ Function: . """
    function_get_instruction_string = _unimplemented_function
    """ Function: . """
    function_get_operand_string = _unimplemented_function
    """ Function: . """
    function_disassemble_one_line = _unimplemented_function
    """ Function: . """
    function_disassemble_as_data = _unimplemented_function
    """ Function: . """
    function_get_default_symbol_name = _unimplemented_function

    def process_instruction_definitions(self, _list):
        pass
        
    def create_duplicated_instruction_entries(self, entry, new_name, operands_string):
        pass


def binary2number(s):
    v = 0
    while len(s):
        v <<= 1
        if s[0] == "1":
            v |= 1
        s = s[1:]
    return v
_b2n = binary2number

def number2binary(v, dynamic_padding=False, padded_length=None):
    s = ""
    while v:
        s = [ "0", "1" ][v & 1] + s
        v >>= 1
    if dynamic_padding:
        w = 4
        while w < len(s):
            w <<= 1
    else:
        w = len(s) if padded_length is None else padded_length
    return "0"*(w-len(s)) + s
_n2b = number2binary

def signed_hex_string(_A, v):
    sign_char = ""
    if v < 0:
        sign_char = "-"
        v = -v
    return sign_char + _A.constant_hexadecimal_prefix + ("%x" % v) + _A.constant_hexadecimal_suffix


def generate_all():
    l = [ "ArchInterface", "_b2n", "_n2b", "_make_specification", "make_operand_mask", "memoize" ]
    for k in globals().keys():
        if k.startswith("II_"):
            l.append(k)
    return l
__all__ = generate_all()
