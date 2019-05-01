'''
=====================
autotagical.filtering
=====================

This is *autotagical.filtering*.

It contains the various functions used to parse filter arrays in *autotagical* and evaluate whether
or not tag arrays match them.

Constants
---------
CONDITION_REGEX
    A compiled regex for parsing the components of a single condition.  Not inteded for use outside
    of this module.

Classes
-------
FilterError(Exception)
    Exception raised when a serious problem is discovered in a filter.

Functions
---------
split_filter_to_conditions(input_filter)
    Takes a single filter and splits it at the and operator: /&|  This function warns if it
    encounters what looks to be a malformed filter using *logging.warning()*.

check_condition(tag_array, condition, categories)
    Takes a list of tags, a single condition to check against, and an *AutotagicalCategories* object
    and determines whether or not the tags match the condition.

check_against_filter(tag_array, single_filter, categories)
    Takes a list of tags, a single filter, and and an *AutotagicalCategories* object and determines
    whether or not the tags match the filter.

check_against_filters(tag_array, filter_array, categories)
    Takes a list of tags, a list of filters, and and an *AutotagicalCategories* object and
    determines whether or not the tags match at least one of the filters.
'''

######################### Imports #########################
import logging
import re

######################### Constants #########################

# Regex for understanding a condition.
CONDITION_REGEX = re.compile(r'^(?P<negated>/!\|)?'
                             r'(?:(?P<wildcard>/\*\|)|'
                             r'(?:/C\|(?P<category>[^/]+))|'
                             r'(?P<tag>[^/]+))$')

######################### Classes #########################
class FilterError(Exception):
    '''Exception raised when a serious problem is discovered in a filter.'''

    def __init__(self, message):
        super().__init__()
        self.message = message

    def __str__(self):
        return str(self.message)

######################### Functions #########################
def split_filter_to_conditions(input_filter):
    '''
    Takes a single filter and splits it at the and operator: /&|  This function warns if it
    encounters what looks to be a malformed filter using *logging.warning()*.

    Parameters
    ----------
    input_filter : str
        A string containing the input filter.  It should be in the form:
        'condition1/&|condition2/&|...'.

    Returns
    -------
    list
        A list of individual conditions to check, each of which must evaluate to True for the
        filter to be true.  It will be in the form: ['condition1', 'condition2', 'condition3', ...]
    '''

    # Confirm that a string is being passed
    if not isinstance(input_filter, str):
        # Log and raise error, as something has gone seriously wrong
        logging.error('A seriously malformed filter was encountered: ' + str(input_filter))
        raise FilterError('Wrong type encountered in filter: ' + str(input_filter) +
                          ' is of type ' + str(type(input_filter)))

    # Split by conditionals
    to_return = input_filter.split('/&|')

    # If any condition is blank, a malformed filter was encountered
    if '' in to_return:
        # Warn about malformed filter
        logging.warning('A malformed filter was encountered: "' + input_filter + '"')
        # Strip it out and continue, since this is a non-fatal error
        to_return = [condition for condition in to_return if condition != '']

    # Return the split conditions
    return to_return

def check_condition(tag_array, condition, categories):
    '''
    Takes a list of tags, a single condition to check against, and an *AutotagicalCategories* object
    and determines whether or not the tags match the condition.

    Parameters
    ----------
    tag_array : list of str
        A list of strings, each holding a tag.  These tags will be considered as a whole against
        the provided filter.  It should be in the form: ['tag1', 'tag2', ...]

    condition : str
        A string with the condition against which the tags will be matched.  This may contain
        various special operators, e.g. the category operator /C|.

    categories : AutotagicalCategories
        An AutotagicalCategories object that will be used to resolve category operators.

    Returns
    -------
    bool
        True if the tags evaluate to true by the condition, False otherwise.
    '''

    # Match the condition
    match = CONDITION_REGEX.match(condition)

    if match:
        # Flip False and True if negated.
        if match.group('negated'):
            match_found = False
        else:
            match_found = True

        # If it's the wild card, it's always true
        if match.group('wildcard'):
            return match_found

        # If it's a tag, see if it's in the array and return accordingly
        if match.group('tag'):
            if match.group('tag') in tag_array:
                return match_found
            return not match_found

        # If it's a category
        if match.group('category'):
            # Load what tags are in that category
            category_tags = categories.get_category_tags(match.group('category'))
            # See if any tag is in the category and return accordingly
            for tag in tag_array:
                if tag in category_tags:
                    return match_found
            return not match_found

    # If here, something went horribly wrong, throw an error
    logging.error('A seriously malformed part of a filter was encountered: "' +
                  str(condition) + '"')
    raise FilterError('Malformed condition encountered: "' + str(condition) + '"')

def check_against_filter(tag_array, single_filter, categories):
    '''
    Takes a list of tags, a single filter, and and an *AutotagicalCategories* object and determines
    whether or not the tags match the filter.

    Parameters
    ----------
    tag_array : list of str
        A list of strings, each holding a tag.  These tags will be considered as a whole against
        the provided filter.  It should be in the form: ['tag1', 'tag2', ...]

    single_filter : str
        A string with the filter against which the tags will be matched.  This may contain
        various special operators, e.g. the category operator /C|, and may be multiple conditions
        concatenated with the and operator /&|.

    categories : AutotagicalCategories
        An AutotagicalCategories object that will be used to resolve category operators.

    Returns
    -------
    bool
        True if the tags match the filter, False otherwise.
    '''

    # Reduce filter to a list of conditions that all must be true for the filter to be matched
    conditions = split_filter_to_conditions(single_filter)

    if not conditions:
        # Completely empty filter.  This is bad.
        logging.error('A filter was completely empty!')
        raise FilterError('Malformed filter encountered: Completely empty!')

    # For each condition, check to see if it's fufilled
    for condition in conditions:
        if not check_condition(tag_array, condition, categories):
            return False

    # If all conditions were successfully cleared, then the filter is passed.
    return True

def check_against_filters(tag_array, filter_array, categories=()):
    '''
    Takes a list of tags, a list of filters, and and an *AutotagicalCategories* object and
    determines whether or not the tags match at least one of the filters.

    Parameters
    ----------
    tag_array : list of str
        A list of strings, each holding a tag.  These tags will be considered as a whole against
        the provided filter.  It should be in the form: ['tag1', 'tag2', ...]

    filter_array : list of str
        A list of strings, each containing a filter against which the tags will be matched.  Each
        may containvarious special operators, e.g. the category operator /C|, and may be multiple
        conditions concatenated with the and operator /&|.

    categories : AutotagicalCategories
        An AutotagicalCategories object that will be used to resolve category operators.

    Returns
    -------
    bool
        True if the tags match at least one filter, False otherwise.
    '''

    if not filter_array:
        # Completely empty filters.  This is bad.
        logging.error('A filter array was completely empty!')
        raise FilterError('Malformed filter array encountered: Completely empty!')

    # Check each filter individually
    for single_filter in filter_array:
        # If a filter is true, no need to check any further.
        if check_against_filter(tag_array, single_filter, categories):
            logging.debug('Tag Array: ' + str(tag_array) + ' matched single filter: ' +
                          str(single_filter) + ' from ' + str(filter_array))
            return True

    # If no one filters were matched, return False
    logging.debug('Tag Array: ' + str(tag_array) + ' did not match and filter in ' +
                  str(filter_array))
    return False
