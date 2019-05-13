"""
===========
autotagical
===========

This is *autotagical*.

It reads in tagged files from one of more input directories then renames and/or
moves them to an output folder hierarchy according to rules specified in user-
provided schemas.  It is intended for use in concert with file tagging
software, e.g. TagSpaces.

-----
Usage
-----
autotagical [-h] [-V] [-C <config file>] [-H] [-i <input path>]
            [-I <ignore file>] [-R] [-o <output path>] [-O]
            [-g <tag group file>] [-s <schema file>] [-A] [--cleanin]
            [--cleanout] [-c] [-F] [-k] [-m] [-M] [-n] [-N] [-t]
            [--debug] [-l <log file>] [-L] [-P] [-q] [-v] [--force]
            [--yes]
"""

__version__ = '1.1.0'  # Define the current version
