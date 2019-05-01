'''
===========
autotagical
===========

This is *autotagical*.

It reads in tagged files from one of more input directories then renames and/or moves them to an
output folder hierarchy according to rules specified in user-provided schemas.  It is intended for
use in concert with file tagging software, e.g. TagSpaces.

-----
Usage
-----
autotagical [-h] [-V] [-C <config file>] [-H] [-i <input path>]
            [-I <ignore file>] [-R] [-o <output path>] [-O]
            [-c <category file>] [-s <schema file>] [-A] [-F] [-k] [-m]
            [-M] [-n] [-N] [-t] [--debug] [-l <log file>] [-L] [-P]
            [-q] [-v] [--force] [--yes]
'''

######################### Constants #########################

__version__ = '1.0.0rc1' # Define the current version
