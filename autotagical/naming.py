'''
==================
autotagical.naming
==================

This is *autotagical.naming*.

It contains the various functions and classes used to parse and generate names based on schema in
autotagical.

---------
Functions
---------
simplify_to_conditionals(format_string)
    Takes a format string and simplifies the "convenience" operators to simply be conditionals.
evaluate_conditionals(format_string, tag_array, categories)
    Takes a format string and evaluates the conditional operators based on the tag array.
strip_iters(format_string)
    Takes a format string and strips all /ITER| tags from it.
evaluate_iters(format_string, occurrences)
    Takes a format string and evaluates any /ITER| operators in it, inserting occurence for the /#|
    operator.
substitute_operators(format_string, file, categories)
    Completely resolve all operators in format_string.  format_string must not contain /ITER|
    operators.

-------
Classes
-------
AutotagicalNamer
    Names files according to a schema.
'''

######################### Imports #########################
import logging
import re
from autotagical.filtering import check_against_filters, check_against_filter
from autotagical.schema import SchemaError

######################### Functions #########################
def simplify_to_conditionals(format_string):
    '''
    Takes a format string and simplifies the "convenience" operators to simply be conditionals.

    Parameters
    ----------
    format_string : str
        The format string may have tag /?T|, category /?C|, conditional /?|, file name /FILE|, tags
        /TAGS|, and/or extension /EXT| operators in it.  It may not have the /ITER|
        operator, as this is handled separately.

    Returns
    -------
    str
        A format string with /?T| and /?C| operators simplified into conditionals.
    '''
    # Sub out conditional tag and category operators with the equivalent conditional
    to_return = AutotagicalNamer.tag_regex.sub(r'/?|\g<tag>/T|\g<tag>/F|/E?|', format_string)
    to_return = AutotagicalNamer.cat_regex.sub(r'/?|/C|\g<cat>/T|\g<cat>/F|/E?|', to_return)
    return to_return

def evaluate_conditionals(format_string, tag_array, categories):
    '''
    Takes a format string and evaluates the conditional operators based on the tag array.

    Parameters
    ----------
    format_string : str
        The format string may have conditional /?|, file name /FILE|, tags /TAGS|, and/or extension
        /EXT| operators in it.  It may not have the /ITER| operator, as this is handled separately.
    tag_array : list of str
        A list of strings, each representing a tag on the file being evaluated.
    categories : AutotagicalCategories
        An AutotagicalCategories object, representing known category groups.

    Returns
    -------
    str
        A format string with all conditional operators evaluated out.
    '''

    to_return = format_string

    # Iterate through all conditionals
    for match in AutotagicalNamer.conditional_regex.finditer(format_string):
        # If the filter is true, replace with true text, otherwise false text
        if check_against_filter(tag_array, match.group('filter'), categories):
            to_return = to_return.replace(match.group('full_conditional'),
                                          match.group('true_sub'), 1)
        else:
            to_return = to_return.replace(match.group('full_conditional'),
                                          match.group('false_sub'), 1)
    return to_return

def strip_iters(format_string):
    '''
    Takes a format string and strips all /ITER| tags from it.

    Parameters
    ----------
    format_string : str
        The format string may have the tag /?T|, category /?C|, conditional /?|, file name
        /FILE|, tags /TAGS|, extension /EXT|, and/or /ITER| operators in it.

    Returns
    -------
    str
        A format string with all /ITER| operators removed.
    '''
    # Strip out iter operators
    stripped = AutotagicalNamer.iter_regex.sub('', format_string)
    # Check that the occurrence operator does not occur outside of iter
    if '/#|' in stripped:
        logging.error('Encountered /#| occurrence operator outside of /ITER| operator!  This will '
                      'lead to files being renamed properly.')
        raise SchemaError('Occurrence /#| operator outside of /ITER| operator!')
    return stripped

def evaluate_iters(format_string, occurrence):
    '''
    Takes a format string and evaluates any /ITER| operators in it, inserting occurence for the /#|
    operator.

    Parameters
    ----------
    format_string : str
        The format string may have the tag /?T|, category /?C|, conditional /?|, file name
        /FILE|, tags /TAGS|, extension /EXT|, and/or /ITER| operators in it
    occurrence : int
        Number of times the file name has been produced (will be inserted for the /#| occurrence
        operator)

    Returns
    -------
    str
        A format string with all /ITER| operators evaluated out.
    '''
    # Substitute in iter text first
    to_return = AutotagicalNamer.iter_regex.sub(r'\g<iter_sub>', format_string)

    # Now need to deal with replacing the /#|'s.
    # If there aren't any, this is bad practice.
    if '/#|' not in to_return:
        logging.warning('Encountered format string with /ITER| operator but no /#|.  This is bad '
                        'and will lead to files not being renamed/moved properly: %s',
                        format_string)
    # Replace and return
    return to_return.replace('/#|', str(occurrence))

def substitute_operators(format_string, file, categories):
    '''
    Takes a format string without /ITER| operators, an AutotagicalFile object, and an
    AutotagicalCategories object, and fully evaluates all operators within the format string.

    Parameters
    ----------
    format_string : str
        The format string may have tag /?T|, category /?C|, conditional /?|, file name /FILE|, tags
        /TAGS|, and/or extension /EXT| operators in it.  It may not have the /ITER| operator, as
        this is handled separately.
    file : AutotagicalFile
        The file to be considered.
    categories : AutotagicalCategories
        An AutotagicalCategories object, representing known category groups.

    Returns
    -------
    str
        The determined output filename.
    '''

    # If the format string is completely empty, something is horribly wrong.
    if not format_string:
        logging.error('Completely empty format string!')
        raise SchemaError('Completely empty format string!')

    # First handle all conditionals by simplifying then evaluating
    to_return = evaluate_conditionals(simplify_to_conditionals(format_string),
                                      file.tag_array, categories)

    # Warn if no extension or no tags
    if '/TAGS|' not in to_return:
        logging.warning('Renamed a file without preserving tags!  This can lead to loss of '
                        'tagging.  Based on format string: %s', format_string)
    if '/EXT|' not in to_return:
        logging.warning('Renamed a file without preserving original extension, based on format '
                        'string: %s', format_string)

    # Anything that is left are simple replacement operators, so sub them all
    to_return = to_return.replace('/EXT|', file.extension)
    to_return = to_return.replace('/TAGS|', file.tags)
    to_return = to_return.replace('/FILE|', file.name)

    # Check if there are any /'s left, as this is a very bad sign.
    if '/' in to_return:
        logging.warning('A "/" is still in the format string after reducing all operators!  '
                        'This probably means there was a problem with the format string!\n'
                        'Format String: ' + format_string + '\nOutput: ' + to_return)

    # If the operators evaluated to a completely blank string, this is bad, because can't use that
    if not to_return:
        logging.error('Completely empty format string after operators: %s', format_string)
        raise SchemaError('Completely empty format string after operators: ' + format_string)

    return to_return

######################### Classes #########################
class AutotagicalNamer:
    '''
    Names files according to a schema.

    Class Attributes
    ----------------
    tag_regex : Regular Expression Object
        Compiled regex for finding /?T| tag operators
    cat_regex : Regular Expression Objects
        Compiled regex for finding /?C| category operators
    conditional_regex : Regular Expression Objects
        Compiled regex for finding /?| conditional operators
    iter_regex : Regular Expression Objects
        Compiled regex for finding /ITER| operators

    Instance Attributes
    -------------------
    __produced_names : dict
        A dictionary with strings for keys and dictionaries for values, containing filenames that
        have been produced (used for iter operators).  It should be of the following form:
            {
                "iterless filename" : dict
                    A dictionary representing a single file name that has been produced.  It should
                    be of the following form:
                        {
                            'occurrences' : int,
                                Number of times this name has been produced
                            'first_occurrence' : str
                                Full path to the first file to be named this
                        }
                ...
            }
    __unnamed_patterns : list of Regular Expression Objects
        List of compiled regexes that define unnamed files.
    __renaming_schema : list of dict
        List of dictionaries, each with strings as keys.  It will be of the form:
        [
            {
                'filters' : list of str
                    ['filter1', 'filter2', ...]
                'format_string' : str
                    'renaming format string containing operators, e.g /?|tag1/T|true/F|false/E?|'
            }
        ]

    Methods
    -------
    __init__(renaming_schema, unnamed_patterns)
        Constructor.  Compiles necessary regexes and initializes attributes.

    check_if_unnamed(file_name)
        Takes a (tagless) file name and determines whether or not it matches any of the unnamed
        patterns known by the class.

    find_format_string(tag_array, categories)
        Takes a file's tag array and finds the first matching renaming schema.

    determine_names(file_list, categories, force_name=False)
        Takes a list of files and processes how they should be renamed according to
        loaded schema.
    '''

    # Regexes used to evaluate the more complx operators
    tag_regex = re.compile(r'(?:/\?T\|(?P<tag>[^/]+?)/\|)')
    cat_regex = re.compile(r'(?:/\?C\|(?P<cat>[^/]+?)/\|)')
    conditional_regex = re.compile(r'(?P<full_conditional>/\?\|(?P<filter>.+?)/T\|'
                                   r'(?P<true_sub>.*?)/F\|(?P<false_sub>.*?)/E\?\|)')
    iter_regex = re.compile(r'(?P<full_iter>/ITER\|(?P<iter_sub>.*?)/EITER\|)')

    def __init__(self, renaming_schema, unnamed_patterns):
        '''
        Constructor.  Compiles necessary regexes and initializes attributes.

        Parameters
        ----------
        renaming_schema : list
            List of the sort stored in AutotagicalSchema.renaming_schemas
        unnamed_patterns : list
            List of the sort stored in AutotagicalSchema.unnamed_patterns

        Returns
        -------
        AutotagicalNamer
        '''
        # Initialize instance attributes to empty
        self.__produced_names = dict()
        self.__unnamed_patterns = []

        # Confirm that empty parameters were not received
        if not renaming_schema:
            logging.error('Completely empty renaming schema!')
            raise SchemaError('Completely empty renaming schema!')
        if not unnamed_patterns:
            logging.error('Completely empty unnamed file schema!')
            raise SchemaError('Completely empty unnamed file schema!')

        # Store schema and compile regexes
        self.__renaming_schemas = renaming_schema
        for pattern in unnamed_patterns:
            self.__unnamed_patterns.append(re.compile(pattern))

    def check_if_unnamed(self, file_name):
        '''
        Takes a (tagless) file name and determines whether or not it matches any of the unnamed
        patterns known by the class.

        Parameters
        ----------
        file_name : str
            The file name to check against the patterns.  This should not contain tags.

        Returns
        -------
        bool
            True if the file is unnamed, False otherwise.
        '''

        # See if file matches any known unnamed pattern and return accordingly
        for regex in self.__unnamed_patterns:
            if regex.match(file_name):
                return True
        return False

    def find_format_string(self, tag_array, categories):
        '''
        Takes a file's tag array and finds the first matching renaming schema.

        Parameters
        ----------
        tag_array : list of str
            A list of strings, each representing a tag on the file.

        categories : AutotagicalCategories
            Known category groups.

        Returns
        -------
        False or str
            False if no matching schema, otherwise format string.
        '''
        # Check if tags match any renaming filter and return the first that does (because priority)
        for schema in self.__renaming_schemas:
            if check_against_filters(tag_array, schema['filters'], categories):
                return schema['format_string']
        return False

    # pylint: disable=too-many-arguments
    def determine_names(self, file_list, categories, force_name=False, force_fail_bad=False,
                        clear_occurrences=False):
        '''
        Takes a list of files and processes how they should be renamed according to
        loaded schema.

        Parameters
        ----------
        file_list : list of AutotagicalFile
            A list of AutotagicalFile objects, each representing a file to be named.
        categories : AutotagicalCategories
            An AutotagicalFile object representing known category groups.
        force_name : bool (False by default)
            Whether to try to rename files that do not match the unnamed pattern.
        force_fail_bad : bool (False by default)
            Whether a manually named file (being named because of force_name) not matching any
            naming schema should be considered a failure to name the file.
        clear_occurrences : bool (False by default)
            Whether to reset produced file names before the run (resetting iter operators).

        Returns
        -------
        list of AutotagicalFile
            A list of AutotagicalFile objects, each representing a file (will include all original
            files).  The 'rename_failed' and 'output_name' attributed will have been set properly.
        '''

        # Initialize list of files to return
        return_list = []

        # Wipe produceed file names, if told to, to reset iter operators
        if clear_occurrences:
            self.__produced_names = dict()

        # Iterate through files
        for file in file_list:
            # First, see if it's been manually named
            unnamed = self.check_if_unnamed(file.name + file.extension)
            if force_name or unnamed:
                # If it's unnamed or we're force naming, then try to rename it
                # Find the right renaming schema
                format_string = self.find_format_string(file.tag_array, categories)

                if not format_string:
                    if not unnamed and not force_fail_bad:
                        # File was manually named, and while it couldn't be renamed, that's okay
                        logging.info('Skipped renaming of manually-named file:\n%s',
                                     file.original_path)
                        file.rename_failed = False
                        return_list.append(file)
                        continue
                    # Otherwise, couldn't name file and that's bad
                    logging.warning('File did not match any renaming schema:\n%s', file.raw_name)
                    file.rename_failed = True
                    return_list.append(file)
                    continue

                # If the file did match a schema, try renaming without /ITER| first
                iterless_name = substitute_operators(strip_iters(format_string), file, categories)

                # Append file path so as to ensure no needless invocation of iter
                produced = str(file.dest_folder) + iterless_name

                # Check if file name has been produced before
                if produced not in self.__produced_names:
                    # First time, remember the name
                    file.output_name = iterless_name
                    file.rename_failed = False
                    return_list.append(file)
                    logging.debug('Scheduling file:\n%s\nto be renamed to:\n%s\nThis is the first '
                                  'time this name has been scheduled.', file.raw_name,
                                  iterless_name)
                    self.__produced_names[produced] = {'first_occurrence' : file.original_path,
                                                       'occurrences' : 1}
                    continue

                # If here, then duplicated name found.  Need to rename original if first time
                logging.debug('Duplicate file name: %s  Invoking ITER operator.', iterless_name)
                if self.__produced_names[produced]['occurrences'] == 1:
                    logging.debug('First duplicate; scheduling rename of first occurrence.')
                    for orig_file in return_list:
                        # Find the first example
                        if orig_file.original_path == \
                            self.__produced_names[produced]['first_occurrence']:
                            # Rename with invoked iter operators
                            orig_file.output_name = substitute_operators(evaluate_iters( \
                                                        format_string, 1), orig_file, \
                                                       categories)
                            logging.debug('Due to dupe, file to be named: ' + iterless_name +
                                          ' now scheduled for: ' + orig_file.output_name)
                            break

                # Increment number of times we've seen the name
                self.__produced_names[produced]['occurrences'] += 1
                # Name current file with iter now
                iter_name = substitute_operators(evaluate_iters(format_string, \
                                                 self.__produced_names[produced]['occurrences']), \
                                                 file, categories)
                file.output_name = iter_name
                file.rename_failed = False
                return_list.append(file)
                logging.debug('Scheduling file:\n' + file.raw_name + '\nto be renamed to:'
                              '\n' + iter_name)
                continue

            # If we got here, then file was manually named
            logging.info('Skipped renaming of manually-named file:\n%s', file.original_path)
            file.rename_failed = False
            return_list.append(file)

        return return_list
