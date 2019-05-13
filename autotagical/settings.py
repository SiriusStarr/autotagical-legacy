"""
====================
autotagical.settings
====================

This is *autotagical.settings*.

It contains the *AutotagicalSettings class and logging setup functions used in
autotagical.

---------
Functions
---------
_init_logging(verbose, no_warn, debug, log_file=None, overwrite_log=False)
    Initialize logging based on settings.  The most verbose option will be
    honored.
_flatten_input_list(input_list)
    Flattens a list of the form returned by argparse.
_load_files(input_list, load_function):
    Loads all provided files with the provided function (while appending)
_check_for_config_file(folder_list):
    Checks all provided folders for a .autotagrc file and returns the path to
    it if found (or None if none).

-------
Classes
-------
AutotagicalSettings
    Loads and holds all settings for a run of autotagical and handles user
    input.
"""

import argparse
import re
import os
import sys
import logging
from autotagical.groups import AutotagicalGroups
from autotagical.schema import AutotagicalSchema
from autotagical import __version__ as version


def _init_logging(verbose, no_warn, debug, log_file=None, overwrite_log=False):
    """
    Initialize logging based on settings.  The most verbose option will be
    honored.

    Parameters
    ----------
    verbose: bool
        Sets log level to at least INFO if True
    no_warn: bool
        Sets log level to ERROR if True and no other flags
    debug: bool
        Sets log level to DEBUG if True
    log_file: str (default None)
        Path to log file to output to
    overwrite_log: bool (default False)
        Whether to overwrite or append to specified log file.

    Returns
    -------
    None
    """
    logging_settings = dict()
    # Set up logging level.  Most verbose option will be honored.
    logging_settings['level'] = logging.WARN
    if no_warn:
        logging_settings['level'] = logging.ERROR
    if verbose:
        logging_settings['level'] = logging.INFO
    if debug:
        logging_settings['level'] = logging.DEBUG

    # Set up log file options, if specified
    if log_file:
        logging_settings['filename'] = log_file[0]
    if overwrite_log:
        if not log_file:
            print('Received the --overwritelog option but a log file was not '
                  'specified.  Ignoring it.')
        else:
            logging_settings['filemode'] = 'w'

    # Set a prettier format for log messages
    logging_settings['format'] = '%(asctime)s - %(levelname)s: %(message)s'

    # Initialize logging
    logging.basicConfig(**logging_settings)


def _flatten_input_list(input_list):
    """
    Flattens a list of the form returned by argparse.

    Parameters
    ----------
    input_list: list
        A list of the form:
            [[data1], [data2], [data3], ...]

    Returns
    -------
    list
        Flattened list, which will be of the form:
            [data1, data2, data3, ...]
    """
    return [item[0] for item in input_list]


def _load_files(input_list, load_function):
    """
    Loads all provided files with the provided function (while appending)

    Parameters
    ----------
    input_list: list of str
        List of paths to files to load.
    load_function: function
        The function to load with.
    """
    for file_name in _flatten_input_list(input_list):
        load_function(file_name, True)


def _check_for_config_file(folder_list):
    """
    Checks all provided folders for a .autotagrc file and returns the path to
    it if found (or None if none).

    Parameters
    ----------
    folder_list: list of str
        List of paths to folders to check.

    Returns
    -------
    str or None
        Path to the first located config file
    """
    for folder in _flatten_input_list(folder_list):
        if os.path.exists(os.path.join(folder, '.autotagrc')):
            return os.path.join(folder, '.autotagrc')
    return None


class AutotagicalSettings:  # pylint: disable=R0902, R0903
    """
    Loads and holds all settings for a run of autotagical and handles user
    input.

    Class Attributes
    ----------------
    yes_regex: Regular Expression Object
        Matches "yes"; used to parse user input
    no_regex: Regular Expression Object
        Matches "no"; used to parse user input

    Instance Attributes
    -------------------
    all_match_root: bool
        Whether to move files that did not match any movement schema, using the
        root output folder for such cases.
    answer_yes: bool
        Whether to assume "yes" for all user prompts.
    tag_groups: AutotagicalGroups
        An AutotagicalGroups object, representing known tag groups.
    clean_folders: list of str
        List of folders to clean (delete empty directories from) after run.
    clobber: bool
        Whether to clobber files in the output folder (overwrite them without
        prompt).
    copy: bool
        Whether to copy files from input folder or move them out of it.
    force_move: bool
        Whether to move files that could not be renamed.
    force_name: bool
        Whether to try to rename even files that have been manually named.
    force_name_fail_bad: bool
        Whether failing to rename a manually-named file counts as failing to
        name.
    ignore_files: list of str
        List of paths to files containing patterns of files to ignore.
    input_folders: list of str
        List of paths to directories to parse files from.
    move_only: bool
        Whether to only move files, not rename them.
    output_folders: list of str
        List of paths to directories to output files to.  Files will be copied
        to each.
    process_hidden: bool
        Whether to include hidden files and directories (those begining with
        ".") in input
        folders.
    recurse: bool
        Whether to descend into subdirectories looking for input files.
    rename_only: bool
        Whether to only rename files, not move them.
    schema: AutotagicalSchema
        A representation of loaded movement/renaming schemas.
    silence_windows: bool
        Whether to silence warnings about unsafe characters in file names for
        Windows.
    trial_run: bool
        Whether to only print actions rather than execute them.

    Methods
    -------
    __init__()
        Constructor; loads all autotagical settings from command line and
        config files.
    get_yes_no(msg, default_to)
        Prompts the user for yes/no input and returns the answer.
    __interpret_args(cl_args, file_args)
        Resolves conflicts between command line and config file settings and
        stores settings.
    __load_args_and_config()
        Load settings from command line and config files.
    """

    yes_regex = re.compile(r'(?i)[y](es)?')
    no_regex = re.compile(r'(?i)[n]o?')

    def __init__(self):
        """
        Constructor; loads all autotagical settings from command line and
        config files.
        """
        self.process_hidden = True
        self.input_folders = []
        self.ignore_files = []
        self.recurse = True
        self.output_folders = []
        self.tag_groups = None
        self.schema = None
        self.all_match_root = True
        self.clean_folders = []
        self.copy = True
        self.move_only = True
        self.rename_only = True
        self.force_move = True
        self.force_name = True
        self.trial_run = True
        self.silence_windows = True
        self.force_name_fail_bad = True
        # Unsafe options initialize to False, because cannot be set via config
        self.clobber = False
        self.answer_yes = False

        # Load in all settings
        self.__load_args_and_config()

    def get_yes_no(self, msg, default_to):
        """
        Prompts the user for yes/no input and returns the answer.

        Parameters
        ----------
        msg: string
            The message to prompt the user with.
        default_to: bool
            Whether to default to "yes" (True) of "no" (False)

        Returns
        -------
        bool
            True if answer is "Yes", False if "No".
        """

        # Don't ask user if we have -y flag
        if self.answer_yes:
            return True

        # Adjust input message based on what answer will default to
        if default_to:
            input_msg = '[n/Y]: '
        else:
            input_msg = '[N/y]: '

        # Get user input
        answer = input(msg + '  ' + input_msg)

        # Match to yes or no or fail to default
        if AutotagicalSettings.yes_regex.fullmatch(answer):
            return True
        if AutotagicalSettings.no_regex.fullmatch(answer):
            return False
        return default_to

    # pylint: disable=R0912, R0915
    def __interpret_args(self, cl_args, file_args):
        """
        Resolves conflicts between command line and config file settings and
        stores settings.

        Parameters
        ----------
        cl_args: Namespace
            Namespace produced by arparse's parse_args() function on the
            command line.
        file_args: Namespace
            Namespace produced by arparse's parse_args() function on a config
            file.

        Returns
        -------
        None
        """
        # Logging
        # Only use config file logging options if none on the command line
        if not cl_args.verbose and not cl_args.no_warn and not cl_args.debug:
            verbose = file_args.verbose
            no_warn = file_args.no_warn
            debug = file_args.debug
        else:
            verbose = cl_args.verbose
            no_warn = cl_args.no_warn
            debug = cl_args.debug
        # Use log file from config if we didn't get one on command line
        overwrite = cl_args.overwrite_log
        log_file = cl_args.log_file
        if not cl_args.log_file:
            log_file = file_args.log_file
            # Only use config overwrite if no log from command line
            if not cl_args.overwrite_log:
                overwrite = file_args.overwrite_log
        # Initialize logging with determined settings
        _init_logging(verbose, no_warn, debug, log_file, overwrite)

        # Input Arguments
        # Process hidden to false only if neither CL nor file set it.
        if not cl_args.process_hidden and not file_args.process_hidden:
            self.process_hidden = False
        logging.debug('Process hidden files/directories: %s',
                      str(self.process_hidden))

        # Use input folders from CL if got them, otherwise file, otherwise fail
        if cl_args.input_folders:
            self.input_folders = _flatten_input_list(cl_args.input_folders)
        elif file_args.input_folders:
            self.input_folders = _flatten_input_list(file_args.input_folders)
        else:
            logging.error('No input folders specified!  Exiting...')
            sys.exit()
        logging.debug('Input folders: %s', str(self.input_folders))

        # Use ignore from command line if got any, otherwise file.
        if cl_args.ignore_files:
            self.ignore_files = _flatten_input_list(cl_args.ignore_files)
        else:
            self.ignore_files = _flatten_input_list(file_args.ignore_files)
        logging.debug('Ignore files: %s', str(self.ignore_files))

        # Recurse to false only if neither set it.
        if not cl_args.recurse and not file_args.recurse:
            self.recurse = False
        logging.debug('Recursive input: %s', str(self.recurse))

        # Output Arguments
        if cl_args.output_folders:
            self.output_folders = _flatten_input_list(cl_args.output_folders)
            if cl_args.organize:
                logging.warning('Both output folders and -O specified on '
                                'command line.  Ignoring -O.')
        elif (cl_args.organize
              or (file_args.organize and not file_args.output_folders)):
            self.output_folders = [self.input_folders[0]]
            logging.info('Organizing files into: %s',
                         str(self.input_folders[0]))
        elif file_args.output_folders:
            self.output_folders = _flatten_input_list(file_args.output_folders)
            if file_args.organize:
                logging.warning('Both output folders and -O specified in '
                                'config file.  Ignoring -O.')
        else:
            logging.error('Neither output folders nor -O specified!  Exiting.')
            sys.exit()
        logging.debug('Output folders: %s', str(self.output_folders))

        # Schema Arguments
        self.tag_groups = AutotagicalGroups()
        if cl_args.tag_group_files:
            _load_files(cl_args.tag_group_files,
                        self.tag_groups.load_tag_groups_from_file)
        else:
            _load_files(file_args.tag_group_files,
                        self.tag_groups.load_tag_groups_from_file)

        # Process groups to resolve fancy features.
        self.tag_groups.process_groups()
        logging.debug('Tag Groups:\n%s', str(self.tag_groups))

        self.schema = AutotagicalSchema()
        if cl_args.schema_files:
            _load_files(cl_args.schema_files,
                        self.schema.load_schema_from_file)
        elif file_args.schema_files:
            _load_files(file_args.schema_files,
                        self.schema.load_schema_from_file)
        else:
            logging.error('No schema specified!  Exiting.')
            sys.exit()
        logging.debug('Schema:\n%s', str(self.schema))

        # Functionality Arguments
        # All match root to false only if neither set it.
        if not cl_args.all_match_root and not file_args.all_match_root:
            self.all_match_root = False
        logging.debug('All match at root: %s', str(self.all_match_root))

        # Clean input only if told to on command line or told in config file
        # and no cleaning on command line.
        # pylint: disable=C0330
        if (cl_args.clean_both
            or cl_args.clean_input_folders
            or (not cl_args.clean_output_folders
                and (file_args.clean_input_folders
                     or file_args.clean_both))):
            self.clean_folders += self.input_folders
        if (cl_args.clean_both
            or cl_args.clean_output_folders
            or (not cl_args.clean_input_folders
                and (file_args.clean_output_folders
                     or file_args.clean_both))):
            self.clean_folders += self.output_folders

        # Keep originals to false only if neither set it.
        if not cl_args.copy and not file_args.copy:
            self.copy = False
        else:
            # Warn if keeping and organizing.
            for in_folder in self.input_folders:
                if in_folder in self.output_folders:
                    logging.warning('Organizing in place with the -k option '
                                    'will lead to file duplcation!  Ignoring '
                                    'the -k option.')
                    self.copy = False
                    break
        logging.debug('Copy files: %s', str(self.copy))

        # Move only unless neither set
        if not cl_args.move_only and not file_args.move_only:
            self.move_only = False
        logging.debug('Only move files: %s', str(self.move_only))

        # Name only unless neither set
        if not cl_args.rename_only and not file_args.rename_only:
            self.rename_only = False
        logging.debug('Only rename files: %s', str(self.rename_only))

        # Doesn't make sense to set both name only and move only
        if self.move_only and self.rename_only:
            self.move_only = False
            self.rename_only = False
            logging.warning('Received both -m and -n options.  This is bad '
                            'practice.  Leave off both instead.')
            logging.debug('Files will be moved and renamed.')

        # Move all unless neither set
        if not cl_args.force_move and not file_args.force_move:
            self.force_move = False
        elif self.rename_only:
            logging.warning('Received the -M option but only renaming files '
                            '(-n).  Ignoring it.')
        logging.debug('Move unnamed files: %s', str(self.force_move))

        # Force name unless neither set
        if not cl_args.force_name and not file_args.force_name:
            self.force_name = False
        elif self.move_only:
            logging.warning('Received the -N option but only moving files '
                            '(-m).  Ignoring it.')
        logging.debug('Try to rename all: %s', str(self.force_name))

        # Force name fail bad unless neither set
        if not cl_args.force_name_fail_bad and \
           not file_args.force_name_fail_bad:
            self.force_name_fail_bad = False
        logging.debug('Force name failure counts as failure: %s',
                      str(self.force_name_fail_bad))

        # Trial run unless neither set
        if not cl_args.trial_run and not file_args.trial_run:
            self.trial_run = False
        logging.debug('Trial run: %s', str(self.trial_run))

        # Silence Windows unless neither set
        if not cl_args.silence_windows and not file_args.silence_windows:
            self.silence_windows = False
        logging.debug('Silence Windows-specific warnings: %s',
                      str(self.silence_windows))

        # Unsafe Arguments
        # Unsafe options may only be set via command line
        if cl_args.clobber:
            self.clobber = True
            logging.warning('Clobbering files in destination!  This is not '
                            'safe.')
        if cl_args.answer_yes:
            self.answer_yes = True
            logging.warning('Answering "yes" to all prompts.  This is unsafe.')

        if file_args.clobber or file_args.answer_yes:
            logging.warning('Unsafe options (--force and/or --yes) have no '
                            'effect in config files. Set via command line if '
                            'you want this behavior.')

    # pylint: disable=R0914
    def __load_args_and_config(self):
        """
        Load settings from command line and config files.
        """
        # Specify help message
        help_msg = ('This is "autotagical".\n\nIt reads in tagged files from '
                    'one of more input directories then renames and/or moves '
                    'them to an output folder hierarchy according to rules '
                    'specified in user-provided schemas.  It is intended for '
                    'use in concert with file tagging software, e.g. '
                    'TagSpaces.')
        # Specify version message
        version_string = ('autotagical v' + version + '  (Tag Group File v' +
                          AutotagicalGroups.TAG_GROUP_FILE_VERSION +
                          ', Schema File v' +
                          AutotagicalSchema.SCHEMA_FILE_VERSION +
                          ', Compat. TagSpaces Settings v' +
                          str(AutotagicalGroups.TAGSPACES_SETTINGS_VERSION)
                          + ', Compat. TagSpaces v' +
                          AutotagicalGroups.TAGSPACES_APP_VERSION + ')')

        # Define an argument parser
        parser = argparse.ArgumentParser(prog='autotagical',
                                         description=help_msg, add_help=False)

        # "Help" arguments
        help_args = parser.add_argument_group('Help')
        help_args.add_argument('-h', '--help', action='help',
                               help='Show this help message and exit.')
        help_args.add_argument('-V', '--version', action='version',
                               version=version_string,
                               help='Print current version message and exit.')
        # Config args
        config_args = parser.add_argument_group('Config')
        config_args.add_argument('-C', '--config', dest='config_file',
                                 action='store', metavar='<config file>',
                                 help='Load config file at specified path.')
        # Input args
        input_args = parser.add_argument_group('Input Options')
        input_args.add_argument('-H', '--hidden', dest='process_hidden',
                                action='store_true',
                                help='Process hidden files (and directories, '
                                     'if -R is specified).')
        input_args.add_argument('-i', '--input', dest='input_folders',
                                action='append', nargs=1,
                                metavar='<input path>', default=[],
                                help='Path to a folder with input files.  May '
                                     'be specified more than once.')
        input_args.add_argument('-I', '--ignore', dest='ignore_files',
                                action='append', nargs=1, default=[],
                                metavar='<ignore file>',
                                help='Path to file patterns (regex format) to '
                                     'ignore (each on new line).  May be '
                                     'specified more than once.')
        input_args.add_argument('-R', '--recursive', dest='recurse',
                                action='store_true',
                                help='Load files recursively from input '
                                     'folders, i.e. descend into subfolders.')
        # Output args
        output_args = parser.add_argument_group('Output Options')
        output_args.add_argument('-o', '--output', dest='output_folders',
                                 action='append', nargs=1, default=[],
                                 metavar='<output path>',
                                 help='Path to a root folder to output files '
                                      'to.  May be specified more than once '
                                      '(output will be duplicated to each).')
        output_args.add_argument('-O', '--organize', dest='organize',
                                 action='store_true',
                                 help='Organize files in place (i.e. use the '
                                      'first input folder for output).  Often '
                                      'used with -R.')
        # Schema args
        schema_args = parser.add_argument_group('Schema Options')
        schema_args.add_argument('-g', '--groups', dest='tag_group_files',
                                 action='append', nargs=1, default=[],
                                 metavar='<tag group file>',
                                 help='Path to a file to read tag groups from.'
                                      '  May be specified more than once '
                                      '(groups will be combined).  '
                                      'TagSpaces or autotagical format.')
        schema_args.add_argument('-s', '--schema', dest='schema_files',
                                 action='append', nargs=1,
                                 metavar='<schema file>',
                                 help='Path to a schema file to move/rename '
                                      'based on.  May be specified more than '
                                      'once (prioritizes first specified).')
        # Functionality args
        function_args = parser.add_argument_group('Functionality Modifiers')
        function_args.add_argument('-A', '--allmatchroot',
                                   dest='all_match_root', action='store_true',
                                   help='Makes root of output folder match '
                                        'all tags, i.e. every file will be '
                                        'moved to output folder, even if it '
                                        'does not match more specifically.')
        function_args.add_argument('--cleanin',
                                   dest='clean_input_folders',
                                   action='store_true',
                                   help='Clean up (delete) all empty folders '
                                        'in input folders (will recurse).')
        function_args.add_argument('--cleanout',
                                   dest='clean_output_folders',
                                   action='store_true',
                                   help='Clean up (delete) all empty folders '
                                        'in output folders (will recurse).')
        function_args.add_argument('-c', '--clean',
                                   dest='clean_both',
                                   action='store_true',
                                   help='Clean up (delete) all empty folders '
                                        'in input and output folders (will '
                                        'recurse).')
        function_args.add_argument('-F', '--failforcerename',
                                   dest='force_name_fail_bad',
                                   action='store_true',
                                   help='Indicates that failing to rename a '
                                        'manually named file should be '
                                        'considered a failure to name the file'
                                        ' (and it should not be moved unless '
                                        '-M is set).')
        function_args.add_argument('-k', '--keep', dest='copy',
                                   action='store_true',
                                   help='Keep original files by copying rather'
                                        ' than moving them.')
        function_args.add_argument('-m', '--move', dest='move_only',
                                   action='store_true',
                                   help='Only move files, do not try to rename'
                                        ' them.')
        function_args.add_argument('-M', '--moveall', dest='force_move',
                                   action='store_true',
                                   help='Move all files, even ones that could '
                                        'not be renamed.')
        function_args.add_argument('-n', '--name', dest='rename_only',
                                   action='store_true',
                                   help='Only rename files, do not try to move'
                                   ' them.')
        function_args.add_argument('-N', '--renamemanual', dest='force_name',
                                   action='store_true',
                                   help='Try to rename all files, not just '
                                        'those matching an unnamed filter.')
        function_args.add_argument('-t', '--trial', dest='trial_run',
                                   action='store_true',
                                   help='Do not actually move or rename files,'
                                        ' just log what  would happen.  '
                                        'Combine with -v to check output '
                                        'before live run.')
        # Logging args
        logging_args = parser.add_argument_group('Logging Options')
        logging_args.add_argument('--debug', dest='debug', action='store_true',
                                  help='Print everything.  This should almost '
                                       'never be used.')
        logging_args.add_argument('-l', '--log', dest='log_file', nargs=1,
                                  metavar='<log file>',
                                  help='Log output to the specified log file. '
                                       ' Usually used with -v.')
        logging_args.add_argument('-L', '--overwritelog', dest='overwrite_log',
                                  action='store_true',
                                  help='Overwrite specified log file rather '
                                       'than append to it.')
        logging_args.add_argument('-P', '--posix', dest='silence_windows',
                                  action='store_true',
                                  help='Silence warnings about invalid '
                                       'characters for Windows filesystems.')
        logging_args.add_argument('-q', '--quiet', dest='no_warn',
                                  action='store_true',
                                  help='Quiet mode.  Do not print warnings, '
                                       'only errors (not recommended).')
        logging_args.add_argument('-v', '--verbose', dest='verbose',
                                  action='store_true',
                                  help='Print all actions taken.  This will '
                                       'list every single file moved/renamed, '
                                       'instead of only warning about '
                                       'failures.')
        # Unsafe args
        unsafe_args = parser.add_argument_group('Dangerous Options')
        unsafe_args.add_argument('--force', dest='clobber',
                                 action='store_true',
                                 help='Force move/rename files, even if there '
                                      'is a file in the  way.  Warning: This '
                                      'will clobber files; use at your own '
                                      'risk, as data loss can occur.')
        unsafe_args.add_argument('--yes', dest='answer_yes',
                                 action='store_true',
                                 help='Assume "yes" to all prompts.  Warning: '
                                      ' Use at your own risk.  (Implies '
                                      '--force)')

        # Determine arguments from command line
        cl_args = parser.parse_args()

        # Try to load config file
        config_file_path = ''
        file_data = []
        # First from location specified on CL
        if cl_args.config_file:
            config_file_path = cl_args.config_file
        else:
            config_file_path = _check_for_config_file(cl_args.output_folders +
                                                      cl_args.input_folders)
            # Then from autotagical's own directory
            if not config_file_path:
                if os.path.exists(os.path.join(os.path.dirname(__file__),
                                               '.autotagrc')):
                    config_file_path = os.path.join(os.path.dirname(__file__),
                                                    '.autotagrc')

        # If found a config file anywhere, load it or fail helpfully
        if config_file_path:
            try:
                with open(config_file_path, 'r') as config_file:
                    file_data = config_file.readlines()
            except IOError:
                print('Could not open config file at: ' + config_file_path)
                sys.exit()

        # Determine args from config file
        file_args = parser.parse_args([arg for line in file_data
                                       for arg in line.split()])

        # Interpret args based on what was received from CL and from config
        # file (if there was one)
        self.__interpret_args(cl_args, file_args)
