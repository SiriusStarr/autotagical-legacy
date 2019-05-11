"""
==================
autotagical.groups
==================

This is *autotagical.groups*.

It contains the *AutotagicalGroups* class, used to load and work with tag
groups.

Classes
-------
AutotagicalGroups
    Holds tag group data and knows how to load it from various sources.
"""

import logging
import json
import sys
import os
from jsonschema import validate, ValidationError
from packaging import version


class AutotagicalGroups:
    """
    Holds tag groups, produces them, and knows how to load them from various
    sources.

    Class Attributes
    ----------------
    TAG_GROUP_FILE_VERSION
        Defines the most up-to-date autotagical tag group format known.
    TAGSPACES_SETTINGS_VERSION
        Defines the most up-to-date TagSpaces tag group format known.
    TAGSPACES_APP_VERSION
        Defines the most up-to-date TagSpaces tag group format known.

    Instance Attributes
    -------------------
    __group_data: dict
        A dictionary with strings as keys, represnting tag group names, and
        values that are sets of strings, each representing a tag.  It should be
        in the form:
        {
            'group 1': set of str
                {'tag1', 'tag2', ...}
            'group 2': set of str
                {'tag3', 'tag4', ...},
        }
    tag_group_schema: dict
        The JSON schema against which to validate autotagical tag group files.
    tagspaces_schema : dict
        The JSON schema against which to validate TagSpaces tag group files.

    Methods
    -------
    __init__()
        Constructor, initializes tag group dictionary and loads validation
        schemas.
    __repr__(self)
        Pretty print tag group data.  Only for debugging.
    get_tags_in_group(group)
        Returns all tags in a specified tag group.
    load_autotagical_format(json_input, append=False)
        Loads tag groups from JSON data in the *autotagical* format.  This does
        not validate the data, as this should be handled upstream.
    load_tagspaces_format(json_input, append=False)
        Loads tag groups from JSON data in the *TagSpaces* format.  This does
        not validate the data, as this should be handled upstream.
    load_tag_groups(json_input, append=False)
        Loads tag groups from JSON data.  This validates against known schemas
        to ensure the data structure is correct.
    load_tag_groups_from_string(file_path, append=False)
        Loads tag groups from JSON data in a string.  This validates against
        known schemas to ensure the data structure is correct.
    load_tag_groups_from_file(file_path, append=False)
        Loads tag groups from JSON data in a file.  This validates against
        known schemas to ensure the data structure is correct.
    """

    TAG_GROUP_FILE_VERSION = "1.0"
    TAGSPACES_SETTINGS_VERSION = 3
    TAGSPACES_APP_VERSION = "3.1.4"

    def __init__(self):
        """
        Constructor, initializes tag group dictionary and loads validation
        schemas.
        """

        self.__group_data = dict()  # Initialize tag group dictionary

        # Load autotagical tag group validation schema or fail with message
        try:
            with open(os.path.join(os.path.dirname(__file__), 'json_schema',
                                   'tag_group_file_schema.json'), 'r') \
                 as tag_group_schema_file:
                self.tag_group_schema = json.load(tag_group_schema_file)
        except IOError:
            logging.error('Tag group file schema missing or cannot be opened! '
                          ' Installation of autotagical is corrupt!')
            sys.exit()
        except json.decoder.JSONDecodeError as err:
            logging.error('Tag group file schema is wholly corrupt!  '
                          'Installation of autotagical is corrupt!  JSON '
                          'error:\nAt line %s, column %s the following error '
                          'was encountered:\n%s', str(err.colno),
                          str(err.lineno), str(err.msg))
            sys.exit()

        # Load TagSpaces tag group validation schema or fail with message
        try:
            with open(os.path.join(os.path.dirname(__file__), 'json_schema',
                                   'tagspaces_tag_group_schema.json'), 'r') \
                 as tagspaces_schema_file:
                self.tagspaces_schema = json.load(tagspaces_schema_file)
        except IOError:
            logging.error('TagSpaces tag group file schema is missing or '
                          'cannot be opened!  Installation of autotagical is '
                          'corrupt!')
            sys.exit()
        except json.decoder.JSONDecodeError as err:
            logging.error('TagSpaces tag group file schema is wholly corrupt! '
                          ' Installation of autotagical is corrupt!  JSON '
                          'error:\nAt line %s, column %s the following error '
                          'was encountered:\n%s', str(err.lineno),
                          str(err.colno), str(err.msg))
            sys.exit()

        logging.debug('Loaded autotagical and TagSpaces tag group file '
                      'schemas.')

    def __repr__(self):
        """
        Pretty print tag group data.  Only for debugging.
        """
        to_return = '-----Tag Groups----\n'
        for group_name, group_tags in sorted(self.__group_data.items()):
            to_return += ('  ' + group_name + ': ' + str(sorted(group_tags)) +
                          '\n')
        to_return += '-----End Tag Groups-----'
        return to_return

    def get_tags_in_group(self, group):
        """
        Returns all tags in a specified tag group.

        Parameters
        ----------
        group: str
            A string consisting of the tag group name to return tags for.

        Returns
        -------
        set
            A set of tags associated with the tag group.  It will be in the
            form:
                {'tag1', 'tag2', 'tag3', ...}
        """

        # Check if group exists, print error if it doesn't and return empty.
        if group not in self.__group_data:
            logging.warning('Malformed condition encountered: Tag group "%s" '
                            'is not among loaded tag groups', str(group))
            return set()
        # Otherwise return the tag group data.
        return self.__group_data[group]

    def load_autotagical_format(self, json_input, append=False):
        """
        Loads tag groups from JSON data in the *autotagical* format.  This does
        not validate the data, as this should be handled upstream.

        Parameters
        ----------
        json_data : dict
            A complex dictionary produced from parsing JSON.  It should be in
            the form:
                {
                    "file_type" : "autotagical_tag_groups",
                    "tag_group_file_version" : 1.0,
                    "tag_groups" : [
                        {
                            "name" : "<group_name>",
                            "tags" : ["<tag1>", "<tag2>",...]
                        },
                        ...
                    ]
                }
        append : bool (default False)
            If True, tag group data is added to previously loaded groups.
            Otherwise, loaded tag groups are wiped first and then replaced.

        Returns
        -------
        bool
            True if load succesful, False otherwise.
        """
        # Receiving schema-validated data, so only need to check version
        if version.parse(str(json_input['tag_group_file_version'])) < \
           version.parse('1.0'):
            logging.error('Error in tag group data: Nonsense version number.')
            return False
        if version.parse(str(json_input['tag_group_file_version'])) > \
           version.parse(AutotagicalGroups.TAG_GROUP_FILE_VERSION):
            logging.error('Error in tag group data: Newer file format found.  '
                          'Update autotagical to continue!')
            return False

        # If not told to append, wipe out extant tag groups
        if not append:
            self.__group_data = dict()

        for group in json_input['tag_groups']:
            # Bad practice to have the same group multiple times, so warn but
            # don't fail
            if group['name'] in self.__group_data:
                logging.warning('Tag group "%s" multiply defined!  Already '
                                'have: "%s", appending to this: "%s"',
                                group['name'],
                                str(self.__group_data[group['name']]),
                                str(group['tags']))
                # Append if already seen
                self.__group_data[group['name']].update(group['tags'])
            else:
                # Otherwise add tag group
                self.__group_data[group['name']] = set(group['tags'])

        logging.debug('Loaded tag groups from autotagical format:\n%s',
                      str(self.__group_data))
        # Loading was successful, so return True
        return True

    def load_tagspaces_format(self, json_input, append=False):
        """
        A function that loads tag groups from JSON data according to TagSpaces
        format.

        Parameters
        ----------
        json_input: dict
            A complex dictionary in the TagSpaces format.
        append: bool
            Whether this should replace all known tag groups or be added to
            them.

        Returns
        -------
        bool
            True if load succesful, False otherwise.
        """
        # Receiving schema-validated data, so only need to check version
        if version.parse(json_input['appVersion']) > \
           version.parse(AutotagicalGroups.TAGSPACES_APP_VERSION) or \
           json_input['settingsVersion'] > \
           AutotagicalGroups.TAGSPACES_SETTINGS_VERSION:
            logging.warning('Newer TagSpaces format found; tag group loading '
                            'may fail.  If your autotagical is up-to-date, '
                            'please report this.  Otherwise, update '
                            'autotagical.')

        # If not told to append, wipe out extant groups
        if not append:
            self.__group_data = dict()

        try:
            for group in json_input['tagGroups']:
                # It's bad practice to have the same tag group multiple times,
                # so warn but don't fail
                if group['title'] in self.__group_data:
                    logging.warning('Tag group "%s" multiply defined!  Already'
                                    ' have: "%s", appending to this: "%s"',
                                    group['title'],
                                    str(self.__group_data[group['title']]),
                                    str([tag['title'] for tag in
                                         group['children']]))
                    # Append if already seen
                    self.__group_data[group['title']].update(
                        {tag['title'] for tag in group['children']})
                else:
                    # Otherwise add group
                    self.__group_data[group['title']] = \
                        {tag['title'] for tag in group['children']}
        except KeyError:
            # This may happen if format changes
            logging.error('Error encountered processing TagSpaces file!  '
                          'Please report this and include the file.')
            return False

        logging.debug('Loaded tag groups from TagSpaces format:\n%s',
                      str(self.__group_data))
        # Loading was successful, so return True
        return True

    def load_tag_groups(self, json_input, append=False):
        """
        Loads tag groups from JSON data.  This validates against known schemas
        to ensure the data structure is correct.

        Parameters
        ----------
        json_input : dict
            This consists of the (usually complicated) dict object produced
            from parsing JSON.  It may be in the TagSpace format or the
            autotagical format, which is again noted here:
                {
                    "file_type" : "autotagical_tag_groups",
                    "tag_group_file_version" : "1.0",
                    "tag_groups" : [
                        {
                            "name" : "<group_name>",
                            "tags" : ["<tag1>", "<tag2>",...]
                        },
                        ...
                    ]
                }
        append : bool
            Whether this should replace all known tag groups or be added to
            them.

        Returns
        -------
        bool
            True if load succesful, False otherwise.
        """
        # Try to validate JSON data against the autotagical schema
        try:
            validate(instance=json_input, schema=self.tag_group_schema)
        except ValidationError as err_autotagical:
            # It wasn't valid, so try against the TagSpaces schema or throw a
            # useful error message
            try:
                validate(instance=json_input, schema=self.tagspaces_schema)
            except ValidationError as err_tagspaces:
                # It failed both schemas, so we don't recognize it.
                logging.error('Tag group data does not match any known '
                              'format.\nAutotagical format error: %s at path: '
                              '%s\nTagSpaces format error: %s at path: %s',
                              str(err_autotagical.message),
                              '->'.join([str(element) for element in
                                         err_autotagical.path]),
                              str(err_tagspaces.message),
                              '->'.join([str(element) for element in
                                         err_tagspaces.path]))
                return False

            # It passed the TagSpaces schema, so load it that way
            logging.debug('Found TagSpaces tag group format.')
            return self.load_tagspaces_format(json_input, append)

        # It passed the autotagical schema, so load it that way
        logging.debug('Found autotagical tag group format.')
        return self.load_autotagical_format(json_input, append)

    def load_tag_groups_from_string(self, json_string, append=False):
        """
        Loads tag groups from JSON data in a string.  This validates against
        known schemas to ensure the data structure is correct.

        Parameters
        ----------
        json_string : string
            String containing JSON data to load
        append : bool
            Whether this should replace all known tag groups or be added to
            them.

        Returns
        -------
        bool
            True if load succesful, False otherwise.
        """
        # Try to load the string as JSON
        try:
            json_data = json.loads(json_string)
        except json.decoder.JSONDecodeError as err:
            logging.error('Tag group data is wholly corrupt!  JSON error:\nAt '
                          'line %s, column %s the following error was '
                          'encountered:\n%s', str(err.lineno), str(err.colno),
                          str(err.msg))
            return False

        # If it's valid JSON, pass it to self.load_tag_groups
        logging.debug('Loading tag group data from string: %s', json_string)
        return self.load_tag_groups(json_data, append)

    def load_tag_groups_from_file(self, file_path, append=False):
        """
        Loads tag groups from JSON data in a file.  This validates against
        known schemas to ensure the data structure is correct.

        Parameters
        ----------
        file_path : string
            Path to the file to load.
        append : bool
            Whether this should replace all known tag groups or be added to
            them.

        Returns
        -------
        bool
            True if load succesful, False otherwise.
        """
        # If loading something without JSON extension, may be fine, but bad
        # practice, so warn.
        if file_path[-5:] != '.json':
            logging.warning('Loading a tag group file with the wrong file '
                            'extension: %s  While not  strictly necessary, the'
                            ' extension should be ".json".', file_path)
        # Try to open the file and parse it as JSON or fail with message
        try:
            with open(file_path, 'r') as tag_group_file:
                json_data = json.load(tag_group_file)
        except IOError:
            logging.error('Could not open tag group file at: %s', file_path)
            sys.exit()
        except json.decoder.JSONDecodeError as err:
            logging.error('Tag group file is wholly corrupt!  JSON error:\nAt '
                          'line %s, column %s the following error was '
                          'encountered:\n%s', str(err.lineno), str(err.colno),
                          str(err.msg))
            sys.exit()

        # If it's valid JSON, pass it to self.load_tag_groups
        logging.debug('Loading tag group data from: %s', file_path)
        return self.load_tag_groups(json_data, append)
