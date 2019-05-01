'''
========================
autotagical.file_handler
========================

This is 'autotagical.file_handler'.

It contains the various functions and classes used to handle finding files, moving them,
etc. in autotagical

---------
Functions
---------
move_files(move_list, settings)
    Moves/renames files according to a provided list.

-------
Classes
-------
AutotagicalFile
    A representation of a file in autotagical.  Gets passed around between
    AutotagicalFileHandler and the various functions for moving and renaming files.
AutotagicalFileHandler
    Loads in and stores files according to provided patterns.
'''

######################### Imports #########################
import os
import shutil
import re
import sys
import logging

######################### Functions #########################
def check_windows_compat(name, full_path):
    '''
    Checks a file name and path for Windows-unsafe characters.

    Parameters
    ----------
    name : str
        Name of file (no directories).
    full_path : str
        Full path of the file

    Returns
    -------
    None
    '''
    if any(char in full_path for char in ['<', '>', ':', '"', '|', '?', '*']):
        logging.warning('Unsafe file name/path: ' + full_path + '\nWindows cannot tolerate '
                        'the following characters:  <>:"|?*  If files are to be used with '
                        'Windows, these names must change.  Otherwise, use -P to silence '
                        'Windows-specific warnings.')
    if '\\' in name:
        logging.warning('Unsafe file name: ' + name + '\nWindows cannot tolerate ' + '\\' + 'in '
                        ' file names.  If files are to be used with Windows, these names must '
                        ' change.  Otherwise, use -P to silence Windows-specific warnings.')
    if name[-1] == '.' or name[-1] == ' ':
        logging.warning('Unsafe file name: ' + name + '\nWindows cannot tolerate file names '
                        'that end in a space or a period.  If files are to be used with Windows,'
                        ' these names must  change.  Otherwise, use -P to silence Windows-specific '
                        'warnings.')

def move_files(move_list, settings): # pylint: disable=too-many-branches, too-many-statements
    '''
    Moves/renames files according to a provided list.

    Parameters
    ----------
    move_list : list of AutotagicalFile
        A list of AutotagicalFile objects, each representing a file to be moved/renamed.
    settings : AutotagicalSettings
        An AutotagicalSettings object holding the settings for the movement.

    Returns
    -------
    None
    '''
    # First check that no output folders are files
    for out_folder in settings.output_folders:
        # If there is a file there
        if os.path.isfile(out_folder):
            # Either don't clobber it and fail or remove it before starting.
            if not settings.clobber and not settings.get_yes_no('File exists at output folder '
                                                                'location: ' + out_folder +
                                                                '\nOverwrite?', False):
                logging.error('Aborting due to bad output folder location.')
                sys.exit()
            else:
                logging.warning('Overwriting file at: ' + out_folder)
                os.remove(out_folder)

    # Iterate through files
    for file in move_list: # pylint: disable=too-many-nested-blocks
        # Unless told to move everything, warn about files that don't match
        if not settings.all_match_root and file.move_failed:
            logging.warning('Skipping file as it failed to match any movement schema: ' +
                            file.raw_name)
            continue

        # Unless told to move all, only move if file was renamed
        if not settings.force_move and file.rename_failed:
            logging.warning('Skipping file as it could not be renamed: ' + file.raw_name)
            continue

        # Don't set this until certain file has been moved, so it is not deleted
        moved = False

        # Concatenate output name with destination folder (empty if root directory)
        rel_out_path = os.path.join(file.dest_folder, file.output_name)

        # Copy file to each output folder
        for out_folder in settings.output_folders:
            full_out_path = os.path.join(out_folder, rel_out_path)
            out_dir = os.path.join(out_folder, file.dest_folder)

            # Warn about unsafe characters
            if not settings.silence_windows:
                check_windows_compat(file.output_name, full_out_path)

            # Don't bother clobbering self
            if os.path.normpath(os.path.normcase(full_out_path)) == \
               os.path.normpath(os.path.normcase(file.original_path)):
                logging.info('Skipping moving file onto itself at: ' + file.original_path)
                continue
            logging.info('Moving/renaming file:\nFrom: ' + file.original_path + '\nTo: ' + \
                         full_out_path)
            # Create the destination folder if it doesn't exist
            if not os.path.exists(out_dir):
                logging.info('Creating destination folder: ' + out_dir)
                if not settings.trial_run:
                    os.makedirs(out_dir)

            # Check for clobber
            if os.path.exists(full_out_path):
                # If it's a dir, have to remove it
                if os.path.isdir(full_out_path):
                    # Remove if told to clobber (by settings or user)
                    if (settings.clobber or settings.get_yes_no('Directory exists at: ' +
                                                                full_out_path +
                                                                '\nOverwrite with file?',
                                                                False)) \
                        and not settings.trial_run:
                        try:
                            shutil.rmtree(full_out_path)
                        except (OSError, FileNotFoundError) as err:
                            logging.error('Error removing directory at: ' + full_out_path +
                                          '\n' + str(err))
                            logging.error('Skipping moving file to: ' + full_out_path)
                            continue
                        except: # pylint: disable=bare-except
                            logging.error('An unhandled exception occurred while removing '
                                          'directory at: ' + full_out_path)
                            logging.error('Skipping moving file to: ' + full_out_path)
                            continue
                    else:
                        logging.warning('Skipping to avoid clobbering.')
                        continue
                # Otherwise, skip if told not to clobber (by both settings and user input)
                elif not settings.clobber and not settings.get_yes_no('File exists at: ' +
                                                                      full_out_path +
                                                                      '\nOverwrite?', False):
                    logging.warning('Skipping to avoid clobbering.')
                    continue
                logging.warning('Overwriting file.')

            # Actually move the file (if not trial)
            if not settings.trial_run:
                try:
                    shutil.copy2(file.original_path, full_out_path)
                except (OSError, FileNotFoundError) as err:
                    logging.error('Error copying file to: ' + full_out_path +
                                  '\n' + str(err))
                    logging.error('Skipping moving file to: ' + full_out_path)
                    continue
                except: # pylint: disable=bare-except
                    logging.error('An unhandled exception occurred while copying file to: ' +
                                  full_out_path)
                    logging.error('Skipping moving file to: ' + full_out_path)
                    continue
            moved = True

        # Now that it's been copied everywhere, remove the file (unless keeping or didn't move)
        if not settings.copy and moved:
            # Only remove original if it was successfully moved
            logging.info('Removing original file at: ' + file.original_path)
            if not settings.trial_run:
                os.remove(file.original_path)

######################### Classes #########################
class AutotagicalFile: # pylint: disable=too-many-instance-attributes, too-few-public-methods
    '''
    A representation of a file in autotagical.  Gets passed around between
    AutotagicalFileHandler and the various functions for moving and renaming files.

    Attributes
    ----------
    dest_folder : str
        The folder the file is to be moved to.
    extension : str
        The extension of the original file.
    move_failed : bool
        True is no applicable movement schema was found, False otherwise.
    name : str
        Original file name, less tags and extension.
    original_path : str
        Complete path to original file, including directories and file name.
    output_name : str
        The file name the file is to be renamed to.
    raw_name : str
        The original file name with tags and extension.
    rename_failed : bool
        True if no applicable renaming schema was found, False otherwise.
    tags : str
        Complete tags on the original file, including any delimiters.
    tag_array : list of str
        List of strings, each a tag on the original file.

    Class Methods
    -------------
    load_file(name, path, tag_patterns, ignore_patterns)
        Returns an AutotagicalFile object if the specified file matches a tag pattern and does
        not match any ignore pattern.  Otherwise, returns None, indicating the file should be
        ignored.

    Instance Methods
    ----------------
    __init__(name, tags, extension, tag_array, raw_name, original_path)
        Constructor; should not be called directly.  Use AutotagicalFile.load_file()
    __repr__()
        Pretty print file info.
    '''

    # pylint: disable=too-many-arguments
    def __init__(self, name, tags, extension, tag_array, raw_name, original_path):
        '''
        Constructor; should not be called directly.  Use AutotagicalFile.load_file()

        Parameters
        ----------
        name : str
            Original file name, less tags and extension.
        tags : str
            Complete tags on the original file, including any delimiters.
        extension : str
            The extension of the original file.
        tag_array : list of str
            List of strings, each a tag on the original file.
        raw_name : str
            The original file name with tags and extension.
        original_path : str
            Complete path to original file, including directories and file name.
        '''
        self.dest_folder = '' # The folder to move to ('' to move to root)
        self.extension = extension # Original file extension
        self.move_failed = False # True if no applicable movement schema was found.
        self.name = name # Original file name less tags and extension
        self.original_path = original_path # Complete path to original, including path and file name
        self.output_name = raw_name # File name to move to.  Default to the current one.
        self.raw_name = raw_name # File name with tags and extension
        self.rename_failed = False # True if no applicable renaming schema was found.
        self.tags = tags # Complete tags on original file, including any delimeters
        self.tag_array = tag_array # List of str, each a tag on the file

    def __repr__(self):
        '''
        Pretty print file info.  Only used for debugging.
        '''
        return '-----File-----\n' \
               '  Destination: "' + str(self.dest_folder) + '"\n' \
               '  Extension: "' + self.extension + '"\n' \
               '  Move Failed: ' + str(self.move_failed)  + '\n' \
               '  Name: "' + self.name + '"\n' \
               '  Original Path: "' + self.original_path + '"\n' \
               '  Output Name: "'  + self.output_name + '"\n' \
               '  Raw Name: "' + self.raw_name + '"\n' \
               '  Rename Failed: ' + str(self.rename_failed) + '\n' \
               '  Tags: "' + self.tags + '"\n' \
               '  Tag Array: ' + str(self.tag_array) + '\n-----End File-----'

    @classmethod
    def load_file(cls, name, path, tag_patterns, ignore_patterns):
        '''
        Returns an AutotagicalFile object if the specified file matches a tag pattern and does
        not match any ignore pattern.  Otherwise, returns None, indicating the file should be
        ignored.

        Parameters
        ----------
        name : str
            The full name of the file to load.
        path : str
            Complete path to original file, including directories and file name.
        tag_patterns : list of dict
            List of dictionaries, each of the following form:
                {
                    'tag_pattern' : Regular Expression Object,
                    'tag_split_pattern' : Regular Expression Object
                }
        ignore_patterns : list of Regular Expression Objects
            A list of compiled regexes full-matching file patterns to ignore.

        Returns
        -------
        AutotagicalFile or None
            Returns an AutotagicalFile object if the file was loaded successfully, None if the file
            should be ignored or did not match a tag pattern.
        '''
        # Check file missing
        if not name or not path:
            raise OSError('Tried to load blank file!')
        # Check if file matches any known pattern
        for pattern in tag_patterns:
            match = pattern['tag_pattern'].fullmatch(name)
            # If the file is tagged
            if match:
                # Check it doesn't match any ignore pattern
                for ign_pattern in ignore_patterns:
                    if ign_pattern.fullmatch(name):
                        logging.info('Skipping file due to ignore file: ' + path)
                        return None
                logging.debug('Found file to process: ' + path)
                # Return the file
                return cls(name=match.group('file'), tags=match.group('raw_tags'),
                           extension=match.group('extension'),
                           tag_array=pattern['tag_split_pattern'].split(match.group('tags')),
                           raw_name=name, original_path=path)
        # File was untagged, so return Non
        logging.info('Skipping untagged file: ' + path)
        return None

class AutotagicalFileHandler:
    '''
    Loads in and stores files according to provided patterns.

    Instance Attributes
    -------------------
    __file_list : list of AutotagicalFile
    __ignore_patterns : list of Regular Expression Objects
        A list of compiled regexes full-matching file patterns to ignore.
    __tag_patterns : list of dict
        List of dictionaries, each of the following form:
            {
                'tag_pattern' : Regular Expression Object,
                'tag_split_pattern' : Regular Expression Object
            }

    Methods
    -------
    __init__(tag_formats)
        Constructor.  Initialize attributes and compiles tag pattern regexes.
    load_ignore_file(path)
        Loads in ignore patterns in the specified ignore file, appending them to known patterns.
    check_new(self, name, path):
        Takes a full path to a file and determines whether it represents a new file or one already
        loaded.
    load_folder(input_folder, recurse=False, process_hidden=False)
        Load in all appropriate files in a given folder.
    get_file_list()
        Returns the list of files to process in a format suitable for feeding to
        determine_destination() or AutotagicalNamer.determine_names()
    '''

    def __init__(self, tag_formats):
        '''
        Constructor.  Initialize attributes and compiles tag pattern regexes.

        Parameters
        ----------
        tag_formats
            List of the form stored in AutotagicalSchema.tag_formats

        Returns
        -------
        AutotagicalFileHandler
        '''
        self.__file_list = []
        self.__ignore_patterns = []
        self.__tag_patterns = [{ \
                                'tag_pattern' : re.compile(pattern['tag_pattern']), \
                                'tag_split_pattern' : re.compile(pattern['tag_split_pattern']) \
                               } for pattern in tag_formats]

    def load_ignore_file(self, path):
        '''
        Loads in ignore patterns in the specified ignore file, appending them to known patterns.

        Parameters
        ----------
        path : str
            The complete path to the file, including folders and the complete file name.

        Returns
        -------
        bool
            True if loading was at least partially successful (individual lines can still fail to
            compile).  False if file could not be opened at all.
        '''
        # Try to open file
        try:
            ignore_file = open(path, 'r')
            # For each line
            for line in ignore_file:
                # Try to compile line as a regex or warn
                try:
                    self.__ignore_patterns.append(re.compile(line.strip()))
                except re.error as err:
                    logging.warning('Regex error in ignore file:  ' + line  + str(err))
            ignore_file.close()
            logging.info('Loaded ignore file: ' + path)
            logging.debug('Ignore patterns: ' + str(self.__ignore_patterns))
            return True
        except IOError:
            logging.error('Specified ignore file missing or cannot be opened: ' + path)
        except: # pylint: disable=bare-except
            logging.error('An unhandled execption occured while loading ignore file.')
        return False

    def check_new(self, name, path):
        '''
        Takes a full path to a file and determines whether it represents a new file or one already
        loaded.

        Parameters
        ----------
        name : str
            The full name of the file.
        path : str
            The path to the file (including file name)

        Returns
        -------
        bool
            True if file has not been loaded before, False otherwise.
        '''
        # Check all known files
        for file in self.__file_list:
            # Only need to do more serious checking if file names match
            if file.raw_name == name:
                if os.path.samefile(file.original_path, path):
                    logging.info('Skipping double processing the file at: ' + path)
                    return False
        return True


    def load_folder(self, input_folder, recurse=False, process_hidden=False):
        '''
        Load in all appropriate files in a given folder.

        Parameters
        ----------
        input_folder : str
            Path to folder to load files from.
        recurse : bool
            If True, will descend into subfolders recursively.
        process_hidden : bool
            If True, will process files beginning with '.' and (if recurse is True) descend into
            directories beginning with '.'

        Returns
        -------
        bool
            True if load was successful, False otherwise.
        '''
        try: # pylint: disable=too-many-nested-blocks
            if recurse:
                # If loading recursively, use os.walk
                for root, dirs, files in os.walk(input_folder):
                    if not process_hidden:
                        # If not processing hidden files, remove hidden files and directories from
                        # those to consider.
                        files = [f for f in files if not f[0] == '.']
                        dirs[:] = [d for d in dirs if not d[0] == '.']
                    # Try to load each file and append it to the file list
                    for file in files:
                        # Only load file if it hasn't been encountered before
                        if self.check_new(file, os.path.join(root, file)):
                            to_append = AutotagicalFile.load_file(file, os.path.join(root, file),
                                                                  self.__tag_patterns,
                                                                  self.__ignore_patterns)
                            # If file was loaded, append it to the list
                            if to_append:
                                self.__file_list.append(to_append)
            else:
                # If not loading recursively, use os.scandir
                with os.scandir(input_folder) as entries:
                    for entry in entries:
                        # For each entry, check if it's a file and not hidden (or processing hidden)
                        if entry.is_file() and (process_hidden or not entry.name.startswith('.')):
                            # Only load file if it hasn't been encountered before
                            if self.check_new(entry.name, entry.path):
                                # Try to load it in and append it.
                                to_append = AutotagicalFile.load_file(entry.name, entry.path,
                                                                      self.__tag_patterns,
                                                                      self.__ignore_patterns)
                                # If file was loaded, append it to the list
                                if to_append:
                                    self.__file_list.append(to_append)
        except FileNotFoundError as err:
            logging.error('Error with input folder: ' + str(err))
            return False
        # If no exceptions, return True
        return True

    def get_file_list(self):
        '''
        Returns the list of files to process in a format suitable for feeding to
        determine_destination() or AutotagicalNamer.determine_names()

        Parameters
        ----------
        None

        Returns
        list of Autotagical File
        '''
        return self.__file_list
