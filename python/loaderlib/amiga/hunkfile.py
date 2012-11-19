"""
    Peasauce - interactive disassembler
    Copyright (C) 2012  Richard Tew

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
Todo:
o A range of hunk handling is already written in the old unused code below.  Incorporate it (with testing).
  - HUNK_UNIT, ?
  - HUNK_LIB, ?
  - HUNK_INDEX, ?
  - HUNK_DEBUG, handles many variations
  - HUNK_SYMBOL, complete
  - HUNK_NAME, ?
  - HUNK_EXT, ?

Notes:
o HUNK_UNIT: An object file, as created by compilation, is composed of program units.
o HUNK_HEADER: A load file, as created by linking, lacks external references or program units.
"""

import os
import logging
import sys

from .doshunks import *


logger = logging.getLogger("loader-amiga")


MEMF_ADVISORY = 1<<29
MEMF_CHIP = 1<<30
MEMF_FAST = 1<<31
MEMF_MASK = MEMF_ADVISORY | MEMF_CHIP | MEMF_FAST

MEMF_NAMES = {}
MEMF_NAMES[0] = "ANY"
MEMF_NAMES[MEMF_ADVISORY] = "ADVISORY"
MEMF_NAMES[MEMF_CHIP] = "CHIP"
MEMF_NAMES[MEMF_FAST] = "FAST"


"""
def is_accepted_file_type(word1):
    if word1 == HUNK_UNIT:
        return True
    if False and word1 == HUNK_LIB: # ...
        return True
    if False and word1 == HUNK_HEADER: # ...
        return True
    return False
"""

class HunkFile(object):
    _header_table_size = None
    _first_hunk_slot = None
    _last_hunk_slot = None
    _header_segments = None

    _hunk_segments = None


def load_file(file_info, data_types):
    with open(file_info.file_path, "rb") as f:
        return _process_file(file_info, data_types, f)

def get_hunk_type(data, segment_id):
    return data._hunk_segments[segment_id][0]

def get_hunk_memory_flags(data, segment_id):
    return data._header_segments[segment_id][0]

def _process_file(file_info, data_types, f):
    data = HunkFile()

    hunk_id = data_types.uint32(f.read(4))
    if hunk_id != HUNK_HEADER:
        logger.debug("amiga/hunkfile.py: _process_file: Unrecognised file.")
        return False

    file_offset = f.tell()
    f.seek(0, os.SEEK_END)
    file_length = f.tell()
    f.seek(file_offset, os.SEEK_SET)

    # OS actually fails loading executables if this doesn't just read a NULL longword.
    data._resident_library_names = _read_hunk_strings(file_info, data_types, f)

    data._header_table_size = data_types.uint32(f.read(4))
    data._first_hunk_slot = data_types.uint32(f.read(4))
    data._last_hunk_slot = data_types.uint32(f.read(4))

    l = []
    segment_count = data._header_table_size
    while segment_count:
        slot_long = data_types.uint32(f.read(4))
        hunk_memory_flags = slot_long & 0xE0000000
        hunk_segment_length = (slot_long & 0x3FFFFFFF) * 4
        l.append((hunk_memory_flags, hunk_segment_length))
        segment_count -= 1
    data._header_segments = l

    # Read in segments.
    l = []
    while f.tell() != file_length:
        longword = data_types.uint32(f.read(4))
        # This should be the same as the header segment slot.  The header slot is what is used for the allocations, in any case.
        segment_memory_flags = longword & 0xE0000000
        segment_hunk_id = longword & 0x3FFFFFFF
        data_length = data_types.uint32(f.read(4)) * 4

        if segment_hunk_id == HUNK_CODE or segment_hunk_id == HUNK_DATA:
            data_offset = f.tell()
            f.seek(data_length, os.SEEK_CUR)
        elif segment_hunk_id == HUNK_BSS:
            data_offset = -1
        else:
            logger.debug("hunkfile.py: _process_file: Unexpected leading segment type: %X (%s)", segment_hunk_id, HUNK_NAMES.get(segment_hunk_id, "?"))
            return False

        relocations = []
        hunk_id = data_types.uint32(f.read(4))
        while hunk_id != HUNK_END:
            if hunk_id == HUNK_RELOC32:
                offset_count = data_types.uint32(f.read(4))
                while offset_count > 0:
                    target_hunk_id = data_types.uint32(f.read(4))
                    offsets = []
                    while offset_count > 0:
                        local_offset = data_types.uint32(f.read(4))
                        offsets.append(local_offset)
                        offset_count -= 1
                    offset_count = data_types.uint32(f.read(4))
                    relocations.append((target_hunk_id, offsets))
            elif hunk_id in (HUNK_DREL32, HUNK_RELOC32SHORT, HUNK_ABSRELOC16):
                offset_count = data_types.uint16(f.read(2))
                while offset_count > 0:
                    target_hunk_id = data_types.uint16(f.read(2))
                    offsets = []
                    while offset_count > 0:
                        local_offset = data_types.uint16(f.read(2))
                        offsets.append(local_offset)
                        offset_count -= 1
                    offset_count = data_types.uint16(f.read(2))
                    relocations.append((target_hunk_id, offsets))
                if f.tell() & 2:
                    f.seek(2, os.SEEK_CUR)
            else:
                logger.debug("hunkfile.py: _process_file: Unexpected secondary segment type: %X %s", hunk_id, HUNK_NAMES.get(hunk_id, "?"))
                return False
            hunk_id = data_types.uint32(f.read(4))

        l.append((segment_hunk_id, data_offset, data_length, relocations))

    data._hunk_segments = l

    if len(data._hunk_segments) != len(data._header_segments):
        logger.debug("hunkfile.py: _process_file: header and actual hunks mismatched")
        return False

    file_info.set_file_data(data)

    for i, header_segment in enumerate(data._header_segments):
        hunk_segment = data._hunk_segments[i]
        hunk_id = hunk_segment[0]
        data_offset = hunk_segment[1]
        data_length = hunk_segment[2]
        relocations = hunk_segment[3]
        segment_size = header_segment[1]
        symbols = {}

        if hunk_id == HUNK_CODE:
            file_info.add_code_segment(data_offset, data_length, segment_size, relocations, symbols)
        elif hunk_id == HUNK_DATA:
            file_info.add_data_segment(data_offset, data_length, segment_size, relocations, symbols)
        elif hunk_id == HUNK_BSS:
            file_info.add_bss_segment(data_offset, data_length, segment_size, relocations, symbols)

    return True

def _read_hunk_strings(file_info, data_types, f):
    l = []
    s = _read_hunk_string(file_info, data_types, f)
    while len(s):
        l.append(s)
        s = _read_hunk_string(file_info, data_types, f)
    return l

def _read_hunk_string(file_info, data_types, f, num_longs=None):
    if num_longs is None:
        num_longs = data_types.uint32(f.read(4))
    s = ""
    if num_longs > 0:
        s = f.read(num_longs * 4)
        idx = s.find('\0')
        if idx > -1:
            return s[:idx]
    return s


def print_summary(file_info):
    data = file_info.file_data

    for i, header_segment in enumerate(data._header_segments):
        hunk_segment = data._hunk_segments[i]
        hunk_name = HUNK_NAMES[hunk_segment[0]]
        hunk_data_offset = hunk_segment[1]
        hunk_data_size = hunk_segment[2]
        hunk_relocation_count = len(hunk_segment[3])

        hunk_memory_name = MEMF_NAMES[header_segment[0]]
        hunk_memory_size = header_segment[1]
        print hunk_name, hunk_data_offset, (hunk_data_size, hunk_memory_size), hunk_memory_name, hunk_relocation_count

# ----------------------------------------------------------------------------
# TODO: Incorporate the below above, and test with sample files to verify correctness.

class HunkFile(object):
    def _read_hunk(self, f, idx):
        while 1:
            # ...
            if hunk_id == HUNK_UNIT:
                if idx in self.hunk_type:
                    raise RuntimeError("Error", self.hunk_type[idx])
                self.hunk_type[idx] = hunk_id
                #
                self.unit_name = self._read_hunk_string(f, data_types)
                if DEBUG_LEVEL >= DEBUG_HUNK_VERBOSE:
                    print "HUNK_UNIT", self.unit_name
            # ...
            elif hunk_id == HUNK_LIB:
                if idx in self.hunk_type:
                    raise RuntimeError("Error", self.hunk_type[idx])
                self.hunk_type[idx] = hunk_id
                #
                num_longwords = structures.read_uint32(f)
                if DEBUG_LEVEL >= DEBUG_HUNK_VERBOSE:
                    print "HUNK_LIB"
            elif hunk_id == HUNK_INDEX:
                if idx in self.hunk_type:
                    raise RuntimeError("Error", self.hunk_type[idx])
                if DEBUG_LEVEL >= DEBUG_HUNK_VERBOSE:
                    print "HUNK_INDEX"
                num_longwords = structures.read_uint32(f)
                print num_longwords * 4
                stringblock_length = structures.read_uint16(f)
                data = f.read(stringblock_length)
                print stringblock_length, data[:40]
                a = structures.read_uint16(f)
                b = structures.read_uint16(f)
                print a,b
                1/0
            # ...
            elif hunk_id == HUNK_DEBUG:
                num_longwords = structures.read_uint32(f)
                _pre_file_offset = f.tell() - 8
                _post_file_offset = f.tell() + num_longwords * 4
                char_4 = f.read(4)
                if char_4 == "ODEF":
                    num_lines = structures.read_uint32(f)
                    if DEBUG_LEVEL >= DEBUG_HUNK_VERBOSE:
                        print "  HUNK_DEBUG id=\"%s\" num_lines=%d" % (char_4, num_lines)
                    line_info = []
                    while len(line_info) < num_lines:
                        leading_uint16 = structures.read_uint16(f)
                        if leading_uint16 != 0:
                            raise RuntimeError("Unexpected ODEF value", leading_uint16)
                        sdef_offset = structures.read_uint32(f)
                        hunk_offset = structures.read_uint32(f)
                        line_info.append((sdef_offset, hunk_offset))
                    if f.tell() & 2:
                        f.seek(2, os.SEEK_CUR)
                    char_4 = f.read(4)
                    if char_4 != "SDEF":
                        raise RuntimeError("Expected SDEF, got:", char_4)
                    num_bytes = structures.read_uint32(f)
                    unknown1 = structures.read_uint32(f)
                    if unknown1 != 0:
                        raise RuntimeError("Expected SDEF unknown1=0, got:", unknown1)
                    unknown2 = structures.read_uint16(f)
                    if unknown2 != 0xFFFF:
                        raise RuntimeError("Expected SDEF unknown2=0xFFFF, got:", unknown2)
                    # Read in the source chunk.
                    source_chunk = f.read(num_bytes-2)
                    if f.tell() & 2:
                        f.seek(2, os.SEEK_CUR)
                    unknown3 = structures.read_uint32(f)
                    if unknown3 != 0:
                        raise RuntimeError("Expected SDEF unknown3=0, got:", unknown3)
                else:
                    debug_base = structures.bytes_to_uint32(char_4)
                    debug_id = f.read(4)
                    if debug_id == "HCLN":
                        # TODO: Work out line/offset encoding.
                        num_name_longwords = structures.read_uint32(f)
                        file_name = self._read_hunk_string(f, num_name_longwords)
                        if DEBUG_LEVEL >= DEBUG_HUNK_VERBOSE:
                            print "  HUNK_DEBUG id=\"%s\" base_offset=%d file_name=\"%s\"" % (debug_id, debug_base, file_name)
                        data_longwords = num_longwords - 3 - num_name_longwords
                        if data_longwords:
                            num_lines = structures.read_uint32(f)
                            line_info = []
                            line_number_sum = 0
                            file_offset_sum = debug_base
                            while len(line_info) < num_lines:
                                def _read_hcln_value(f):
                                    value = structures.read_uchar(f)
                                    if value == 0:
                                        value = structures.read_uint16(f)
                                        if value == 0:
                                            value = structures.read_uint32(f)
                                    return value
                                line_number_sum += _read_hcln_value(f)
                                file_offset_sum += _read_hcln_value(f)
                                line_info.append((line_number_sum, file_offset_sum))
                            if f.tell() & 2:
                                f.seek(2, os.SEEK_CUR)
                    elif debug_id == "HEAD":
                        debug_id2 = f.read(8)              # 3                
                        data = f.read((num_longwords - 4) * 4)
                        if DEBUG_LEVEL >= DEBUG_HUNK_VERBOSE:
                            print "  HUNK_DEBUG id=\"%s\" id2=\"%s\" base_offset=%d" % (debug_id, debug_id2, debug_base)
                            text = "    "+ "".join(("%02x" % ord(c)) for c in data[:40])
                            if len(data) > 40:
                                text += "..."
                            print len(text), text
                    elif debug_id == "LINE":
                        num_name_longwords = structures.read_uint32(f)
                        file_name = self._read_hunk_string(f, num_name_longwords)
                        loop_longwords = num_longwords - 3 - num_name_longwords
                        num_line_offsets = loop_longwords / 2
                        while loop_longwords > 0:
                            line_number = structures.read_uint32(f)
                            file_offset = structures.read_uint32(f)
                            loop_longwords -= 2
                            
                        if DEBUG_LEVEL >= DEBUG_HUNK_VERBOSE:
                            print "  HUNK_DEBUG id=\"%s\" base_offset=%d num_line_offsets=%d" % (debug_id, debug_base, num_line_offsets)
                    elif debug_id == "OPTS":
                        opts_value = structures.read_uint32(f)
                        if True or DEBUG_LEVEL >= DEBUG_HUNK_VERBOSE:
                            print "  HUNK_DEBUG id=\"%s\" base_offset=%d value=%x" % (debug_id, debug_base, opts_value)
                    else:
                        print "  HUNK_DEBUG id=\"%s\" base_offset=%d" % (debug_id, debug_base)
                        # Unknown, exit with information.
                        data = f.read(_post_file_offset - f.tell())
                        text = "    "+ "".join(("%02x" % ord(c)) for c in data[:40])
                        if len(data) > 40:
                            text += "..."
                        print text
                        raise RuntimeError("New debug", num_longwords, debug_id, debug_base, hex(_pre_file_offset))
            elif hunk_id == HUNK_SYMBOL:
                symbol_name = self._read_hunk_string(f)
                symbol_value = 0
                if DEBUG_LEVEL >= DEBUG_HUNK_VERBOSE:
                    print "  HUNK_SYMBOL"
                    print "    SYMBOL", "\"%s\"=%x" % (symbol_name, symbol_value)
                while symbol_name:
                    symbol_value = structures.read_uint32(f)
                    if DEBUG_LEVEL >= DEBUG_HUNK_VERBOSE:
                        print "    SYMBOL", "\"%s\"=%x" % (symbol_name, symbol_value)
                    symbol_name = self._read_hunk_string(f)                
            elif hunk_id == HUNK_NAME:
                symbol_name = self._read_hunk_string(f)
                if DEBUG_LEVEL >= DEBUG_HUNK_VERBOSE:
                    print "  HUNK_NAME", symbol_name
            elif hunk_id == HUNK_EXT:
                if DEBUG_LEVEL >= DEBUG_HUNK_VERBOSE:
                    print "  HUNK_EXT"
                name_length = structures.read_uint32(f)
                while name_length != 0:
                    symbol_type = name_length >> 24
                    name_length = name_length & 0x00FFFFFF
                    symbol_name = ""
                    if name_length:
                        symbol_name = self._read_hunk_string(f, name_length)
                    if symbol_type in (EXT_DEF, EXT_ABS, EXT_RES):
                        symbol_value = structures.read_uint32(f)
                        if DEBUG_LEVEL >= DEBUG_HUNK_VERBOSE:
                            print "    EXT_SYMBOL", "TYPE=%s" % EXT_NAMES[symbol_type], "LENGTH=%s" % name_length, "\"%s\"=%x" % (symbol_name, symbol_value)
                    elif symbol_type in (EXT_REF32, EXT_REF16, EXT_REF8, EXT_DEXT32, EXT_DEXT16, EXT_DEXT8):
                        if DEBUG_LEVEL >= DEBUG_HUNK_VERBOSE:
                            print "    EXT_REFERENCE", "TYPE=%s" % EXT_NAMES[symbol_type], "LENGTH=%s" % name_length, "\"%s\":" % symbol_name
                        reference_index = 0
                        reference_count = structures.read_uint32(f)
                        while reference_index < reference_count:
                            reference_value = structures.read_uint32(f)
                            if DEBUG_LEVEL >= DEBUG_HUNK_VERBOSE:
                                print "      "+ hex(reference_value)
                            reference_index += 1
                    #elif symbol_type == EXT_COMMON:
                    #    pass
                    else: # , EXT_RELREF32, EXT_RELREF26
                        raise RuntimeError("Unknown symbol_type", hex(symbol_type))
                        
                    name_length = structures.read_uint32(f)