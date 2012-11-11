# Peasauce Disassembler

## Support

If you need to email me, perhaps to mention your rich royal Nigerian diplomat uncle who needs access to my bank account, my email address is:

 richard.m.tew@gmail.com

If you wish to generally support or encourage the development of this tool, or sponsor the development of specific features, [Paypal donations](http://disinterest.org/donate.html) will be used for that purpose.  For those who are serious about sponsoring development of a specific feature it is best to discuss it with me at my email address first.

## Goal

The current primary goal is to handle disassembling Amiga m68000 executables. Support for the wider family of m680x0 instructions, or executables for other platforms that used these chips is within scope, in order to drive better code structure for later expansion to other architectures or platforms.

Using Resource to disassemble within an Amiga emulator is still a wonderful experience, however it has aged.  It is not possible to modify it, and it is also nowhere near as nice as being able to use a proper application in your
own operating system.

## Features

Peasauce can currently do the following:

* Load and attempt to disassemble Amiga executable files.
* Load and attempt to disassemble Atari ST executable files.
* Load and attempt to disassemble X60000 executable files.
* Attempt to disassemble loaded M60000 code

Note that there are limitations, files which include unsupported assembly code or use special executable file features may among other things not get loaded, or disassembled fully.

## Licensing

All files that comprise this are released under the GPLv3 license.

Any source code contributions must be made by the sole author of those
contributions, and be contributed with dual licensing under both the
MIT and GPLv3 license.  At some point in the future, I may wish to
use parts of this in commercial projects, or switch the license of the
open source project as a whole to the more liberal MIT license.

## Installation

Currently Peasauce is prototyped in Python.

1. Download and install [Python 2.7](http://python.org/download/) for your platform.
2. Download and install [wxPython for Python 2.7](http://www.wxpython.org/download.php) for your platform.

## Usage

Once you have Peasauce installed, run it's "run.py" Python script.

You should be able to use the user interface to:
* Load and disassemble a new file.
* Scroll through a loaded and disassembled file.
* Change the font used to a smaller or non-proportional one.

## Future Work

This is intended to be a summarised list of short points that briefly note intended work, or possible future work.

### Short Term

#### Bugs

* UI: Should split blocks based on known symbols before any disassembly (BSS addresses good example).
* UI: Should split blocks on address discovery.
* UI: Address extraction from disassembly match should not happen in UI, as UI should not be m68k specific.
* UI: Disassembly text label placement should not happen in UI, as UI should not be m68k specific.
* UI: Label placement should consider the case where a value happens to match a known address, like how Resource has #START+$50, where that might actually be $50 or whatever.

#### Functionality

* Disassembly: Display DBRA instead of DBF (is this right?).
* Disassembly: Customisable display of either A7 or SP.
* Disassembly: Jump table discovery / processing.
* Disassembly: Verify used EA mode against instructions declared valid list.
* Disassembly: Research assembler syntax for different platforms, to generalise custom output.
* Disassembly: Choose use of new or old style assembly syntax.
* File loading: For Amiga, choose use of "DATA, CHIP" or "DATA_C" in section headers.
* UI: Ala Resource, change the datatype of a block.
* UI: Ala Resource, change the numeric base of a value.
* UI: Enable user doing disassembly work, with editing actions.
* UI: Export source code.
* UI: Research a UI toolkit that better suits an editing interface.
* UI: File-backed storage space should optionally use aggregate instructions, e.g. "dcb.l 230,0"
* UI: Add leading comments that detail file type, processor, entry point offset.. maybe more.

#### Optimisation

* UI: Lots of lines virtually displayed means a slow/sluggish wx UI.

#### Technical Debt

* Coding style: Better error propagation, no exception raising on purpose.
* Coding style: Make code / system interaction more straightforward.
* Disassembly: Do a correct formatting check on the instruction table II_NAME column.
* File loading: Clean up file_info.file_data to only store useful information.

### Medium Term

#### Functionality

* Debugging: Connect to WinUAE and select from and debug running processes.
* Debugging: Connect to WinUAE, browse files, and select a file to run and debug.
* Decompilation: Look into IRs.  LLVM?
* Disassembly: Handle more / differentiate between different M680x0 instructions.

### Long Term

#### Functionality

* Disassembly: Support ARM instructions.
* Disassembly: Support PowerPC instructions.
* Disassembly: Support x86 instructions.
* Disassembly: Support x86-64 instructions.
* File loading: Support Amiga library loading.
* File loading: Support Amiga object file loading.
* File loading: Detect and automatically do Amiga decrunching.
* File loading: Support Mac OS X Mach-O executable loading.
* File loading: Support Macintosh m68k PEF loading.
* File loading: Support Windows PE loading.

#### Pie In The Sky

* Disassembly: Generate library signatures and use to jumpstart disassembly.
* UI: Collaborative work on the same file.
* UI: Upload symbols to a remote server and allow merging of work.
