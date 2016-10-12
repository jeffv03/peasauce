
# Returned from file identification to rate confidence in guessed or recognised file format.
MATCH_NONE = 0
MATCH_POSSIBLE = 1
MATCH_PROBABLE = 2
MATCH_CERTAIN = 3

# The supported processors.
PROCESSOR_UNKNOWN = 0
PROCESSOR_M680x0 = 100
PROCESSOR_M68000 = 101
PROCESSOR_M68010 = 102
PROCESSOR_M68020 = 103
PROCESSOR_M68030 = 104
PROCESSOR_M68040 = 105
PROCESSOR_M68060 = 106
PROCESSOR_MIPS = 200
PROCESSOR_65c816 = 300
PROCESSOR_Z80 = 400

processor_names = {
    PROCESSOR_UNKNOWN: "Unknown",
    PROCESSOR_65c816: "65c816",
    PROCESSOR_M680x0: "M680x0",
    PROCESSOR_M68000: "M68000",
    PROCESSOR_M68010: "M68010",
    PROCESSOR_M68020: "M68020",
    PROCESSOR_M68030: "M68030",
    PROCESSOR_M68040: "M68040",
    PROCESSOR_M68060: "M68060",
    PROCESSOR_MIPS: "MIPS",
    PROCESSOR_Z80: "Z80",
}

def lookup_processor_id_by_name(specified_processor_name):
    specified_processor_name = specified_processor_name.lower()
    for processor_id, processor_name in processor_names.iteritems():
        if processor_name.lower() == specified_processor_name:
            return processor_id

# The supported platforms.
PLATFORM_UNKNOWN = 0
PLATFORM_AMIGA = 1000
PLATFORM_ATARIST = 2000
PLATFORM_SNES = 6000
PLATFORM_X68000 = 7000
PLATFORM_ZXSPECTRUM = 8000

platform_names = {
    PLATFORM_UNKNOWN: "Unknown",
    PLATFORM_AMIGA: "Amiga",
    PLATFORM_ATARIST: "Atari ST",
    PLATFORM_SNES: "SNES",
    PLATFORM_X68000: "X68000",
    PLATFORM_ZXSPECTRUM: "ZX Spectrum",
}

# The supported file formats.
FILE_FORMAT_UNKNOWN = 0

FILE_FORMAT_AMIGA_HUNK_EXECUTABLE = PLATFORM_AMIGA + 1
FILE_FORMAT_AMIGA_HUNK_LIBRARY = PLATFORM_AMIGA + 2

FILE_FORMAT_ATARIST_GEMDOS_EXECUTABLE = PLATFORM_ATARIST + 1

FILE_FORMAT_SNES_SMC = PLATFORM_SNES + 1

FILE_FORMAT_X68000_X_EXECUTABLE = PLATFORM_X68000 + 1

FILE_FORMAT_ZXSPECTRUM_Z80_1 = PLATFORM_ZXSPECTRUM + 1
FILE_FORMAT_ZXSPECTRUM_Z80_2 = PLATFORM_ZXSPECTRUM + 2
FILE_FORMAT_ZXSPECTRUM_Z80_3 = PLATFORM_ZXSPECTRUM + 3


file_format_names = {
    FILE_FORMAT_UNKNOWN: "Unknown",

    FILE_FORMAT_AMIGA_HUNK_EXECUTABLE: "Hunk executable",
    FILE_FORMAT_AMIGA_HUNK_LIBRARY: "Hunk library",

    FILE_FORMAT_ATARIST_GEMDOS_EXECUTABLE: "GEMDOS executable",

    FILE_FORMAT_SNES_SMC: "SMC rom",

    FILE_FORMAT_X68000_X_EXECUTABLE: "X executable",

    FILE_FORMAT_ZXSPECTRUM_Z80_1: "Z80 snapshot v1",
    FILE_FORMAT_ZXSPECTRUM_Z80_2: "Z80 snapshot v2",
    FILE_FORMAT_ZXSPECTRUM_Z80_3: "Z80 snapshot v3",
}

ENDIAN_UNKNOWN = 0
ENDIAN_BIG = 1
ENDIAN_LITTLE = 2

endian_names = {
    ENDIAN_UNKNOWN: "Unknown",
    ENDIAN_BIG: "Big",
    ENDIAN_LITTLE: "Little",
}


class MatchResult(object):
    confidence = MATCH_NONE
    platform_id = PLATFORM_UNKNOWN
    file_format_id = FILE_FORMAT_UNKNOWN

def __import_data_types():
    import disassembly_data
    for attr_name in dir(disassembly_data):
        if attr_name.startswith("DATA_TYPE_"):
            globals()[attr_name] = getattr(disassembly_data, attr_name)

__import_data_types()

