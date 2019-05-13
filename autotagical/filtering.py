"""
=====================
autotagical.filtering
=====================

This is *autotagical.filtering*.

It contains the various functions used to parse filters in *autotagical* and
evaluate whether or not tag arrays match them.

Constants
---------
_CONDITION_REGEX
    A compiled regex for parsing the components of a single condition.  Not
    intended for use outside of this module.

Classes
-------
FilterError(Exception)
    Exception raised when a serious problem is discovered in a filter.

Functions
---------
split_condition_set_to_conditions(condition_set)
    Takes a condition set and splits it at the and operator: /&|  This function
    warns if it encounters what looks to be a malformed condition set.
check_condition(tag_array, condition, tag_groups)
    Takes a list of tags, a single condition to check against, and an
    *AutotagicalGroups* object and determines whether or not the tags match
    the condition.
check_against_condition_set(tag_array, condition_set, tag_groups)
    Takes a list of tags, a condition set, and and an *AutotagicalGroups*
    object and determines whether or not the tags match the condition set.
check_against_filter(tag_array, filter, tag_groups)
    Takes a list of tags, a filter, and and an *AutotagicalGroups* object
    and determines whether or not the tags match at least one of the condition
    set.
"""

import logging
import re

# Regex for understanding a condition.
_CONDITION_REGEX = re.compile(r'^(?P<negated>/!\|)?'
                              r'(?:(?P<wildcard>/\*\|)|'
                              r'(?:/G\|(?P<tag_group>[^/]+))|'
                              r'(?P<tag>[^/]+))$')


class FilterError(Exception):
    """Exception raised when a serious problem is discovered in a filter."""

    def __init__(self, message):
        super().__init__()
        self.message = message

    def __str__(self):
        return str(self.message)


def split_condition_set_to_conditions(condition_set):
    """
    Takes a condition set and splits it at the and operator: /&|  This function
    warns if it encounters what looks to be a malformed condition set.

    Parameters
    ----------
    condition_set: str
        A string containing the input condition set.  It should be in the form:
            'condition1/&|condition2/&|...'.

    Returns
    -------
    list
        A list of individual conditions to check, each of which must evaluate
        to True for the condition st to be true.  It will be in the form:
            ['condition1', 'condition2', 'condition3', ...]
    """
    # Split by conditionals
    to_return = condition_set.split('/&|')

    # If any condition is blank, a malformed condition set was encountered
    if '' in to_return:
        # Warn about malformed condition set
        logging.warning('A malformed condition set was encountered: "%s"',
                        condition_set)
        # Strip it out and continue, since this is a non-fatal error
        to_return = [condition for condition in to_return if condition != '']

    # Return the split conditions
    return to_return


def check_condition(tag_array, condition, tag_groups):
    """
    Takes a list of tags, a single condition to check against, and an
    *AutotagicalGroups* object and determines whether or not the tags match the
    condition.

    Parameters
    ----------
    tag_array: list of str
        A list of strings, each holding a tag.  These tags will be considered
        as a whole against the provided condition.  It should be in the form:
            ['tag1', 'tag2', ...]
    condition: str
        A string with the condition against which the tags will be matched.
        This may contain various special operators.
    tag_groups: AutotagicalGroups
        An AutotagicalGroups object that will be used to resolve tag group
        operators.

    Returns
    -------
    bool
        True if the tags evaluate to true by the condition, False otherwise.
    """

    # Match the condition
    match = _CONDITION_REGEX.match(condition)

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

        # If it's a tag group
        if match.group('tag_group'):
            # See if tags match the group
            if tag_groups.tag_in_group(tag_array, match.group('tag_group')):
                return match_found
            return not match_found

    # If here, something went horribly wrong, throw an error
    logging.error('A seriously malformed condition was encountered: "%s"',
                  str(condition))
    raise FilterError('Malformed condition encountered: "' + str(condition) +
                      '"')


def check_against_condition_set(tag_array, condition_set, tag_groups):
    """
    Takes a list of tags, a condition set, and and an *AutotagicalGroups*
    object and determines whether or not the tags match the condtion set.

    Parameters
    ----------
    tag_array: list of str
        A list of strings, each holding a tag.  These tags will be considered
        as a whole against the provided condition set.  It should be in the
        form: ['tag1', 'tag2', ...]
    condition_set: str
        A string with the condition set against which the tags will be
        matched.  This may contain various special operators, and may be
        multiple conditions concatenated with the AND operator /&|.
    tag_groups: AutotagicalGroups
        An AutotagicalGroups object that will be used to resolve group
        operators.

    Returns
    -------
    bool
        True if the tags match the condition set, False otherwise.
    """

    # Reduce condition set to a list of conditions that all must be true for
    # the condition set to be matched
    conditions = split_condition_set_to_conditions(condition_set)

    if not conditions:
        # Completely empty condition set.  This is bad.
        logging.error('A condition set was completely empty!')
        raise FilterError('Malformed condition set encountered: Completely '
                          'empty!')

    # For each condition, check to see if it's fufilled
    for condition in conditions:
        if not check_condition(tag_array, condition, tag_groups):
            return False

    # If all conditions were cleared, then the condition set is passed.
    return True


def check_against_filter(tag_array, check_filter, tag_groups):
    """
    Takes a list of tags, a filter, and and an *AutotagicalGroup* object and
    determines whether or not the tags match the filter.

    Parameters
    ----------
    tag_array: list of str
        A list of strings, each holding a tag.  These tags will be considered
        as a whole against the provided filter.  It should be in the form:
            ['tag1', 'tag2', ...]
    filter: list of str
        A list of strings, each containing a condition set against which the
        tags will be matched.  Each may contain various special operators and
        may be multiple conditions concatenated with the AND operator /&|.
    tag_groups: AutotagicalGroups
        An AutotagicalGroups object that will be used to resolve group
        operators.

    Returns
    -------
    bool
        True if the tags match at least one filter, False otherwise.
    """

    if not check_filter:
        # Completely empty filter.  This is bad.
        logging.error('A filter was completely empty!')
        raise FilterError('Malformed filter encountered: Completely empty!')

    # Check each condition set individually
    for condition_set in check_filter:
        # If a condition set is true, no need to check any further.
        if check_against_condition_set(tag_array, condition_set, tag_groups):
            logging.debug('Tag Array: %s matched condition set: %s from %s',
                          str(tag_array), str(condition_set),
                          str(check_filter))
            return True

    # If no condition sets were matched, return False
    logging.debug('Tag Array: %s did not match any condition set in %s',
                  str(tag_array), str(check_filter))
    return False
