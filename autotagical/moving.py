'''
==================
autotagical.moving
==================

This is *autotagical.moving*.

It contains the various functions used to generate file organization based on a schema.

---------
Functions
---------
process_filter_level(tag_array, filter_level, categories)
    Takes a file's tag array and a single filter level and determines the contribution to path that
    it and all sublevels contribute by operating recursively.
generate_path(tag_array, movement_schema, categories)
    Takes a file's tag array and determines how to organize it according to a movement schema.
determine_destination(file_list, movement_schema, categories)
    Takes a list of files and processes how they should be organized in directories according to a
    schema.
'''

######################### Imports #########################
import logging
import os
from autotagical.filtering import check_against_filters
from autotagical.schema import SchemaError

######################### Functions #########################
# pylint: disable=too-many-return-statements
def process_filter_level(tag_array, filter_level, categories):
    '''
    Takes a file's tag array and a single filter level and determines the contribution to path that
    it and all sublevels contribute by operating recursively.

    Parameters
    ----------
    tag_array : list of str
        A list of strings, each holding a tag.  These tags will be considered as a whole against
        the provided filter.  It should be in the form: ['tag1', 'tag2', ...]
    filter_level : dict
        A dictionary with strings for keys, representing a single filter level.  It should have the
        following form:
            {
                "filters" : list of str
                    ["filter1", "filter2", ...]
                "subfolder" : str
                    "name of the subfolder (left in parent directory if empty)"
                "subfilters" : list of dict
                    [
                        {
                            "filters" : list of str,
                            "subfolder" : str
                            "subfilters" : list of dict
                        },
                        ...
                    ]
            }
    categories : AutotagicalCategories
        An AutotagicalCategories object that will be used to resolve category operators.

    Returns
    -------
    (full_match, path) : (bool, str)
        full_match : bool
            Whether or not a positive match was found at the lowest level.  Returns False if the
            tag array did not determine a specific location.
        path : str
            The constructed file path from the current level down.  Empty if no matches whatsoever.
    '''

    # Check if it matches the filters at this level
    if check_against_filters(tag_array, filter_level['filters'], categories):
        # If there isn't a subfolder name, it's supposed to go in the "current" (previous) folder
        if not filter_level['subfolder']:
            return (True, '')

        # If there are no subfilters, it's supposed to terminate in the specified subfolder
        if not filter_level['subfilters']:
            return (True, filter_level['subfolder'])

        # partial_sort becomes true if some further matching is found but not a conclusive location
        partial_sort = False
        # Check through all the filters (and recurse) to find a location
        for fil in filter_level['subfilters']:
            # Recurse to check the entire filter tree

            output = process_filter_level(tag_array, fil, categories)
            # If a positive match was found at a lower level, join the output and return True
            if output[0]:
                # Only concatenate if there is actually a subfolder
                if output[1]:
                    return (True, os.path.join(filter_level['subfolder'], output[1]))
                # Otherwise return current path with a conclusive match
                return (True, filter_level['subfolder'])

            # If no positive match was found, but a partial match was, set partial_sort.
            # This only gets set ONCE because filter order determines priority (but a full match)
            # would still be used over it
            if output[1] and not partial_sort:
                partial_sort = output[1]
        # If no exact match was found but a partial was, use the first partial (because priority)
        if partial_sort:
            return (False, os.path.join(filter_level['subfolder'], partial_sort))

        # Otherwise, no matches were found at lower directories
        return (False, filter_level['subfolder'])

    # If we got here, it means that the file didn't even match current filters
    return (False, '')

def generate_path(tag_array, movement_schema, categories):
    '''
    Takes a file's tag array and determines how to organize it according to a movement schema.

    Parameters
    ----------
    tag_array : list of str
        A list of strings, each holding a tag.  These tags will be considered as a whole against
        the provided schema.  It should be in the form: ['tag1', 'tag2', ...]
    movement_schema : list of dict
        A list of dictionaries, each with strings for keys, representing a single filter level.  It
        should have the following form:
            [
                {
                    "filters" : list of str
                        ["filter1", "filter2", ...]
                    "subfolder" : str
                        "name of the subfolder (left in parent directory if empty)"
                    "subfilters" : list of dict
                        [
                            {
                                "filters" : list of str,
                                "subfolder" : str
                                "subfilters" : list of dict
                            },
                            ...
                        ]
                },
                ...
            ]
    categories : AutotagicalCategories
        An AutotagicalCategories object that will be used to resolve category operators.

    Returns
    -------
    (move_failed, path) : (bool, str)
        move_failed : bool
            Whether or not any amount of matching was found.  Returns False if the tag array did not
            determine any location whatsoever and shouldn't be moved.
        path : str
            The constructed file path.  Empty if no matches whatsoever.
    '''
    # partial_sort becomes true if some matching is found but not a conclusive location
    partial_sort = False

    # Completely empty movement_schema.  This is bad.
    if not movement_schema:
        logging.error('Completely empty movement schema!')
        raise SchemaError('Completely empty movement schema!')

    # For every movement schema
    for filter_level in movement_schema:
        # Try to sort according to it
        output = process_filter_level(tag_array, filter_level, categories)
        # If a positive match was found, done (because filter priority)
        if output[0]:
            logging.debug('Good match for moving tags: %s', str(tag_array))
            return (False, output[1])
        # A partial sorting was found; will be used if no exact match is found
        if output[1] and not partial_sort:
            partial_sort = output[1]

    # If we're here, we either found zero matches or a partial sort
    if partial_sort:
        logging.warning('Failed to match a fully specified location for tags:\n%s\nSorted only '
                        'to:\n%s\nThis is bad practice.  Add a /*| operator at that level if you '
                        'intend to catch all files at that point.', str(tag_array), partial_sort)
        return (False, partial_sort)

    # Absolutely no matching whatsoever, so return that it failed
    return (True, '')

def determine_destination(file_list, movement_schema, categories):
    '''
    Takes a list of files and processes how they should be organized in directories according to a
    schema.

    Parameters
    ----------
    file_list : list of AutotagicalFile
        A list of AutotagicalFile objects, each representing a file to be moved.
    movement_schema : list
        A list of movement schema in the form provided by AutotagicalSchema.movement_schemas
    categories : AutotagicalCategories
        An AutotagicalCategories object that will be used to resolve category operators.

    Returns
    -------
    list of AutotagicalFile
        A list of AutotagicalFile objects, each representing a file (will include all original
        files).  The 'move_failed' and 'dest_folder' attributed will have been set properly.
    '''

    # Initialize return list
    return_list = []

    # Loop through all provided files
    for name_file in file_list:
        # Determine the appropriate path
        output = generate_path(name_file.tag_array, movement_schema, categories)

        # Set values accordingly
        name_file.dest_folder = output[1]
        name_file.move_failed = output[0]

        # Warn if no math was found
        if name_file.move_failed:
            logging.warning('File did not match any moving schema:\n%s', str(name_file))

        # Append it to the list
        return_list.append(name_file)

    # Return the list
    return return_list
