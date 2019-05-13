"""
==================
autotagical.schema
==================

This is 'autotagical.schema*.

It contains the AutotagicalSchema class, used to load and work with movement
and renaming schemas.

Functions
---------
_repr_filter_tree(filter, indent=0)
    Pretty print a schema level.  Only used for debugging.

Classes
-------
SchemaError(Exception)
    Exception raised when a serious problem is discovered in a schema file.
AutotagicalSchema
    Holds schema data and knows how to load it from various sources.
"""

import logging
import json
import sys
import os
from jsonschema import validate, ValidationError
from packaging import version


def _repr_filter_tree(filter_level, indent=0):
    """
    Pretty print a schema level.  Only used for debugging.

    Parameters
    ----------
    filter_level: dict
        The filter level to print.  Should have keys 'filter', 'subfolder', and
        'sublevels'.
    indent: int
        The number of spaces to begin indenting by.  Should be a multiple of 2.

    Returns
    -------
    str
        Pretty-printed string containing the current filter level and all
        sublevels (by operating recursively).
    """
    to_return = ''
    to_return += (' ' * indent + 'Filter: ' + str(filter_level['filter']) +
                  '\n')
    to_return += (' ' * indent + 'Subfolder Name: "' +
                  str(filter_level['subfolder']) + '"\n')
    to_return += ' ' * indent + 'Sublevels:\n'
    for subl in filter_level['sublevels']:
        to_return += _repr_filter_tree(subl, indent + 2)
    if to_return[-1] != '\n':
        to_return += '\n'
    return to_return


class SchemaError(Exception):
    """
    Exception raised when a serious problem is discovered in a schema file.
    """

    def __init__(self, message):
        super().__init__()
        self.message = message

    def __str__(self):
        return str(self.message)


class AutotagicalSchema:
    """
    A representation of movement/renaming schemas.  Capable of loading itself
    from various sources.

    Class Attributes
    ----------------
    SCHEMA_FILE_VERSION
        Defines the most up-to-date autotagical schema format known.

    Instance Attributes
    -------------------
    tag_formats: list of dict
        A list of dictionaries, each with strings as keys.  It will be of the
        form:
            [
                {
                    'tag_pattern': str
                        'regex containing groups "file", "raw_tags", "tags",
                         and "extension"'
                    'tag_split_pattern': str
                        'regex to be used with re.split() to separate tags'
                }
            ]
    unnamed_patterns: list
        List of strings, each a regex pattern that defines unnamed files.
    renaming_schemas: list of dict
        List of dictionaries, each with strings as keys.  It will be of the
        form:
            [
                {
                    'filter': list of str
                        ['condition set 1', 'condition set 2', ...]
                    'format_string': str
                        'renaming format string containing operators, e.g
                         /?|tag1/T|true/F|false/E?|'
                }
            ]
    movement_schema: list of dict
        List of dictionaries, each with strings as keys keys.  It will be of
        the form:
            [
                {
                    'filter': list of str
                        ['condition set 1', 'condition set 2', ...]
                    'subfolder': str
                        'subfolder name'
                    'sublevels': list of dict
                    [
                        {additional dict with filter, subfolder, sublevels}
                    ]
                }
            ]

    Methods
    -------
    __init__()
        Constructor; initialize attributes to empty and loads validation schema
    __repr__(self)
        Pretty print schema data.  Only used for debugging.
    load_schema(json_input, append=False)
        Loads movement/renaming schemas from JSON data.  Validates that the
        data matches a known format first.
    load_schema_from_string(json_string, append=False)
        Loads schema from JSON data in a string.  Validates that the data
        matches a known format first.
    load_schema_from_file(file_path, append=False)
        Loads schema from JSON data in a file.  This validates against known
        formats to ensure the data structure is correct.
    """

    SCHEMA_FILE_VERSION = '1.1'

    def __init__(self):
        """
        Constructor, initializes all attributes to blank and loads the
        validation schema.
        """
        # Initialize all attributes to blank.
        self.movement_schema = []
        self.renaming_schemas = []
        self.tag_formats = []
        self.unnamed_patterns = []

        # Load validation schema or fail with message
        try:
            with open(os.path.join(os.path.dirname(__file__), 'json_schema',
                                   'schema_file_schema.json'), 'r') \
                 as schema_file:
                self.schema_file_schema = json.load(schema_file)
        except IOError:
            logging.error('Schema file schema missing or cannot be opened!  '
                          'Installation of autotagical is corrupt!')
            sys.exit()
        except json.decoder.JSONDecodeError as err:
            logging.error('Schema file schema is wholly corrupt!  '
                          'Installation of autotagical is corrupt!  JSON '
                          'error:\nAt line %s, column %s the following error '
                          'was encountered:\n%s', str(err.lineno),
                          str(err.colno), str(err.msg))
            sys.exit()

    def __repr__(self):
        """
        Pretty print schema data.  Only for debugging.
        """
        to_return = '-----Schema-----\n'
        to_return += '  Movement Schema:\n'
        for sch in self.movement_schema:
            to_return += _repr_filter_tree(sch, 4) + '\n'
        to_return += '  Renaming Schemas:\n'
        for sch in self.renaming_schemas:
            to_return += '    Filter: ' + str(sch['filter']) + '\n'
            to_return += ('    Format String: ' + str(sch['format_string']) +
                          '\n    --\n')
        to_return += '  Tag Formats:\n'
        for form in self.tag_formats:
            to_return += '    Tag Pattern: ' + form['tag_pattern'] + '\n'
            to_return += ('    Tag Split Pattern: ' + form['tag_split_pattern']
                          + '\n    --\n')
        to_return += '  Unnamed Patterns:\n'
        for pattern in sorted(self.unnamed_patterns):
            to_return += '    ' + pattern + '\n    --\n'
        to_return += '-----End Schema-----'
        return to_return

    def load_schema(self, json_input, append=False):
        """
        Loads a movement/renaming schema from JSON data.  Validates that the
        data matches a known schema first.

        Parameters
        ----------
        json_input: dict
            A complex dictionary produced from parsing JSON.  It should be in
            the form:
                {
                  'file_type': 'autotagical_schema',
                  'schema_file_version': '1.1',
                  'tag_formats': [
                    {
                      'tag_pattern': 'pattern',
                      'tag_split_pattern': 'pattern'
                    },
                    ...
                  ],
                  'unnamed_patterns': [
                    'pattern',
                    ...
                  ],
                  'renaming_schemas': [
                    {
                      'filter': [
                        '<tag1>',
                        '<tag2>/&|<tag3>',
                        '/G|<group1>',
                        '/!|<tag4>',
                        '/*|'
                      ],
                      'format_string': 'file name with operators'
                    },
                    ...
                  ],
                  'movement_schema': [
                    {
                      'filter': [
                        'condition set 1',
                        'condition set 2',
                        ...
                      ],
                      'subfolder': 'subfolder name',
                      'sublevels': [
                        {
                          'filter': [
                            'condition set 3',
                            'condition set 4',
                            ...
                          ],
                          'subfolder': 'subfolder name',
                          'sublevels': []
                        },
                        ...
                      ]
                    },
                    ...
                  ]
                }

        Returns
        -------
        bool
            True if load succesful, False otherwise.
        """
        # Try to validate JSON data against the schema
        try:
            validate(instance=json_input, schema=self.schema_file_schema)
        except ValidationError as err:
            logging.error('Schema data does not match any known format.\n'
                          'Error: %s at path: %s', str(err.message),
                          '->'.join([str(element) for element in err.path]))
            return False

        # After validation only version requires checking
        if version.parse(json_input['schema_file_version']) < \
           version.parse('1.0'):
            logging.error('Error in schema data: Nonsense version number.')
            return False
        if version.parse(json_input['schema_file_version']) > \
           version.parse(AutotagicalSchema.SCHEMA_FILE_VERSION):
            logging.error('Error in schema data: Newer file format found.  '
                          'Update autotagical to continue!')
            return False

        # If not appending, clear schema
        if not append:
            self.tag_formats = []
            self.unnamed_patterns = []
            self.renaming_schemas = []
            self.movement_schema = []

        # Load in schema
        self.tag_formats += json_input['tag_formats']
        self.unnamed_patterns += json_input['unnamed_patterns']
        self.renaming_schemas += json_input['renaming_schemas']
        self.movement_schema += json_input['movement_schema']

        logging.debug('Loaded schema:\nTag Formats: %s\nUnnamed Patterns:  %s'
                      '\nRenaming Schemas: %s\nMovement Schema: %s',
                      str(self.tag_formats), str(self.unnamed_patterns),
                      str(self.renaming_schemas), str(self.movement_schema))
        return True

    def load_schema_from_string(self, json_string, append=False):
        """
        Loads schema from JSON data in a string.  Validates that the data
        matches a known schema first.

        Parameters
        ----------
        json_string: string
            String containing JSON data to load.  Should be in the format taken
            by AutotagicalSchema.load_schema().

        Returns
        -------
        bool
            True if load succesful, False otherwise.
        """
        # Try to parse as JSON or fail with message
        try:
            json_data = json.loads(json_string)
        except json.decoder.JSONDecodeError as err:
            logging.error('Schema data is wholly corrupt!  JSON error:\nAt '
                          'line %s, column %s the following error was '
                          'encountered:\n%s', str(err.lineno), str(err.colno),
                          str(err.msg))
            return False

        logging.debug('Loading schema data from string: %s', json_string)
        # Pass it to load_schema to see if it actually works and load if so
        return self.load_schema(json_data, append)

    def load_schema_from_file(self, file_path, append=False):
        """
        Loads schema from JSON data in a file.  This validates against known
        formats to ensure the data structure is correct.

        Parameters
        ----------
        file_path: string
            Path to the file to load.  Should contain JSON in the format taken
            by AutotagicalSchema.load_schema().

        Returns
        -------
        bool
            True if load succesful, False otherwise.
        """
        # If loading something without JSON extension, may be fine, but bad
        # practice, so warn.
        if file_path[-5:] != '.json':
            logging.warning('Loading a schema file with the wrong file '
                            'extension: %s  While not strictly necessary, the '
                            'extension should be ".json".', file_path)
        try:
            with open(file_path, 'r') as schema_file:
                json_data = json.load(schema_file)
        except IOError:
            logging.error('Could not open schema file at: %s', file_path)
            sys.exit()
        except json.decoder.JSONDecodeError as err:
            logging.error('Schema file is wholly corrupt!  JSON error:\nAt '
                          'line %s, column %s the following error was '
                          'encountered:\n%s', str(err.lineno), str(err.colno),
                          str(err.msg))
            sys.exit()

        logging.debug('Loading schema data from: %s', file_path)
        # Pass it to load_schema to see if it actually works and load it if so
        return self.load_schema(json_data, append)
