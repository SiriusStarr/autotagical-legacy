'''
======================
autotagical.categories
======================

This is *autotagical.categories*.

It contains the *AutotagicalCategories* class, used to load and work with categories.

Classes
-------
AutotagicalCategories
    Holds category data and knows how to load it from various sources.
'''

######################### Imports #########################
import logging
import json
import sys
import os
from jsonschema import validate, ValidationError
from packaging import version

######################### Classes #########################
class AutotagicalCategories:
    '''
    Holds tag categories, produces them, and knows how to load them from various sources.

    Class Attributes
    ----------------
    CATEGORY_FILE_VERSION
        Defines the most up-to-date autotagical category format known.
    TAGSPACES_SETTINGS_VERSION
        Defines the most up-to-date TagSpaces category format known.
    TAGSPACES_APP_VERSION
        Defines the most up-to-date TagSpaces category format known.

    Instance Attributes
    -------------------
    __cat_data : dict
        A dictionary with strings as keys, represnting category names, and values that are sets of
        strings, each representing a tag.  It should be in the form:
        {
            'category 1' : set of str
                {'tag1', 'tag2', ...}
            'category 2' : set of str
                {'tag3', 'tag4', ...},
        }
    category_schema : dict
        The JSON schema against which to validate autotagical category files.
    tagspaces_schema : dict
        The JSON schema against which to validate TagSpaces tag group files.

    Methods
    -------
    __init__()
        Constructor, initializes category dictionary and loads validation schemas.
    __repr__(self)
        Pretty print category data.  Only for debugging.
    get_category_tags(category)
        Returns all tags in a specified category.
    load_autotagical_format(json_input, append=False)
        Loads categories from JSON data in the *autotagical* format.  This does not validate the
        data, as this should be handled upstream.
    load_tagspaces_format(json_input, append=False)
        Loads categories from JSON data in the *TagSpaces* format.  This does not validate the
        data, as this should be handled upstream.
    load_categories(json_input, append=False)
        Loads categories from JSON data.  This validates against known schemas to ensure the data
        structure is correct.
    load_categories_from_string(file_path, append=False)
        Loads categories from JSON data in a string.  This validates against known schemas to
        ensure the data structure is correct.
    load_categories_from_file(file_path, append=False)
        Loads categories from JSON data in a file.  This validates against known schemas to
        ensure the data structure is correct.
    '''

    CATEGORY_FILE_VERSION = "1.0"
    TAGSPACES_SETTINGS_VERSION = 3
    TAGSPACES_APP_VERSION = "3.1.4"

    def __init__(self):
        '''
        Constructor, initializes category dictionary and loads validation schemas.
        '''

        self.__cat_data = dict() # Initialize category dictionary

        # Load autotagical category validation schema or fail with message
        try:
            with open(os.path.join(os.path.dirname(__file__), 'json_schema',
                                   'category_file_schema.json'), 'r') as cat_schema_file:
                self.category_schema = json.load(cat_schema_file)
        except IOError:
            logging.error('Category file schema missing or cannot be opened!  '
                          'Installation of autotagical is corrupt!')
            sys.exit()
        except json.decoder.JSONDecodeError as err:
            logging.error('Category file schema is wholly corrupt!  Installation of autotagical is '
                          'corrupt!  JSON error:\nAt line %s, column %s the following error was '
                          'encountered:\n%s', str(err.colno), str(err.lineno), str(err.msg))
            sys.exit()
        except: # pylint: disable=bare-except
            logging.error('An unhandled execption occured loading category file schema.')
            sys.exit()

        # Load TagSpaces category validation schema or fail with message
        try:
            with open(os.path.join(os.path.dirname(__file__), 'json_schema',
                                   'tagspaces_category_schema.json'), 'r') as tagspaces_schema_file:
                self.tagspaces_schema = json.load(tagspaces_schema_file)
        except IOError:
            logging.error('TagSpaces category file schema missing or cannot be opened!  '
                          'Installation of autotagical is corrupt!')
            sys.exit()
        except json.decoder.JSONDecodeError as err:
            logging.error('TagSpaces category file schema is wholly corrupt!  Installation of '
                          'autotagical is corrupt!  JSON error:\nAt line %s, column %s the '
                          'following error was encountered:\n%s', str(err.lineno), str(err.colno),
                          str(err.msg))
            sys.exit()
        except: # pylint: disable=bare-except
            logging.error('An unhandled execption occured loading TagSpaces category file schema.')
            sys.exit()

        logging.debug('Loaded category file and TagSpaces category validation schemas.')

    def __repr__(self):
        '''
        Pretty print category data.  Only for debugging.
        '''
        to_return = '-----Categories----\n'
        for cat_name, cat_tags in sorted(self.__cat_data.items()):
            to_return += '  ' + cat_name + ': ' + str(sorted(cat_tags)) + '\n'
        to_return += '-----End Categories-----'
        return to_return

    def get_category_tags(self, category):
        '''
        Returns all tags in a specified category.

        Parameters
        ----------
        category : str
            A string consisting of the category name to return.

        Returns
        -------
        set
            A set of tags associated with the category.  It will be in the form:
            {'tag1', 'tag2', 'tag3', ...}
        '''

        # Check if the category exists, print error if it doesn't and return empty.
        if category not in self.__cat_data:
            logging.warning('Malformed condition encountered: Category "%s" is not among loaded '
                            'categories', str(category))
            return set()
        # Otherwise return the category data.
        return self.__cat_data[category]

    def load_autotagical_format(self, json_input, append=False):
        '''
        Loads categories from JSON data in the *autotagical* format.  This does not validate the
        data, as this should be handled upstream.

        Parameters
        ----------
        json_data : dict
            A complex dictionary produced from parsing JSON.  It should be in the form:
            {
                "file_type" : "autotagical_tag_categories",
                "category_file_version" : 1.0,
                "categories" : [
                    {
                        "name" : "<category_name>",
                        "tags" : ["<tag1>", "<tag2>",...]
                    },
                    ...
                ]
            }

        append : bool (default False)
            If True, category data is added to previously loaded categories.  Otherwise, loaded
            categories are wiped first and then replaced.

        Returns
        -------
        bool
            True if load succesful, False otherwise.
        '''
        # Receiving schema-validated data, so only need to check version
        if version.parse(str(json_input['category_file_version'])) < version.parse('1.0'):
            logging.error('Error in category data: Nonsense version number.')
            return False
        if version.parse(str(json_input['category_file_version'])) > \
           version.parse(AutotagicalCategories.CATEGORY_FILE_VERSION):
            logging.error('Error in category data: Newer file format found.  '
                          'Update autotagical to continue!')
            return False

        # If not told to append, wipe out extant categories
        if not append:
            self.__cat_data = dict()

        for category in json_input['categories']:
            # It's bad practice to have the same category multiple times, so warn but don't fail
            if category['name'] in self.__cat_data:
                logging.warning('Category "%s" multiply defined!  Already have: "%s", appending to '
                                'this: "%s"', category['name'],
                                str(self.__cat_data[category['name']]), str(category['tags']))
                # Append if already seen
                self.__cat_data[category['name']].update(category['tags'])
            else:
                # Otherwise add category
                self.__cat_data[category['name']] = set(category['tags'])

        logging.debug('Loaded categories from autotagical format:\n%s', str(self.__cat_data))
        # Loading was successful, so return True
        return True

    def load_tagspaces_format(self, json_input, append=False):
        '''
        A function that loads categories from JSON data according to TagSpaces format.

        Parameters
        ----------
        json_input : {dictionary in TagSpaces format}

        append : bool
            Whether this should replace all known categories or be added to them.

        Returns
        -------
        bool
            True if load succesful, False otherwise.
        '''
        # Receiving schema-validated data, so only need to check version
        if version.parse(json_input['appVersion']) > \
           version.parse(AutotagicalCategories.TAGSPACES_APP_VERSION) or \
           json_input['settingsVersion'] > AutotagicalCategories.TAGSPACES_SETTINGS_VERSION:
            logging.warning('Newer TagSpaces format found; category loading may fail.  '
                            'If your autotagical is up-to-date, please report this; otherwise '
                            'update autotagical.')

        # If not told to append, wipe out extant categories
        if not append:
            self.__cat_data = dict()

        try:
            for category in json_input['tagGroups']:
                # It's bad practice to have the same category multiple times, so warn but don't fail
                if category['title'] in self.__cat_data:
                    logging.warning('Category "%s" multiply defined!  Already have: "%s", '
                                    'appending to this: "%s"', category['title'],
                                    str(self.__cat_data[category['title']]),
                                    str([tag['title'] for tag in category['children']]))
                    # Append if already seen
                    self.__cat_data[category['title']].update( \
                        {tag['title'] for tag in category['children']})
                else:
                    # Otherwise add category
                    self.__cat_data[category['title']] = \
                        {tag['title'] for tag in category['children']}
        except KeyError:
            # This may happen if format changes
            logging.error('Error encountered processing TagSpaces file!  Please report this and '
                          'include the file.')
            return False

        logging.debug('Loaded categories from TagSpaces format:\n%s', str(self.__cat_data))
        # Loading was successful, so return True
        return True

    def load_categories(self, json_input, append=False):
        '''
        Loads categories from JSON data.  This validates against known schemas to ensure the data
        structure is correct.

        Parameters
        ----------
        json_input : dict
            This consists of the (usually complicated) dict object produced from parsing JSON.  It
            may be in the TagSpace format or the autotagical form, which is again noted here:
            {
                "file_type" : "autotagical_tag_categories",
                "category_file_version" : "1.0",
                "categories" : [
                    {
                        "name" : "<category_name>",
                        "tags" : ["<tag1>", "<tag2>",...]
                    },
                    ...
                ]
            }

        append : bool
            Whether this should replace all known categories or be added to them.

        Returns
        -------
        bool
            True if load succesful, False otherwise.
        '''
        # Try to validate JSON data against the autotagical schema
        try:
            validate(instance=json_input, schema=self.category_schema)
        except ValidationError as err_autotagical:
            # It wasn't valid, so try against the TagSpaces schema or throw a useful error message
            try:
                validate(instance=json_input, schema=self.tagspaces_schema)
            except ValidationError as err_tagspaces:
                # It failed both schemas, so we don't recognize it.
                logging.error('Category data does not match any known format.\nAutotagical Format '
                              'Error: %s at path: %s\nTagSpaces Format Error: %s at path: %s',
                              str(err_autotagical.message),
                              '->'.join([str(element) for element in err_autotagical.path]),
                              str(err_tagspaces.message),
                              '->'.join([str(element) for element in err_tagspaces.path]))
                return False

            # It passed the TagSpaces schema, so load it that way
            logging.debug('Found TagSpaces category format.')
            return self.load_tagspaces_format(json_input, append)

        # It passed the autotagical schema, so load it that way
        logging.debug('Found autotagical category format.')
        return self.load_autotagical_format(json_input, append)

    def load_categories_from_string(self, json_string, append=False):
        '''
        Loads categories from JSON data in a string.  This validates against known schemas to
        ensure the data structure is correct.

        Parameters
        ----------
        json_string : string
            String containing JSON data to load

        append : bool
            Whether this should replace all known categories or be added to them.

        Returns
        -------
        bool
            True if load succesful, False otherwise.
        '''
        # Try to load the string as JSON
        try:
            json_data = json.loads(json_string)
        except json.decoder.JSONDecodeError as err:
            logging.error('Category data is wholly corrupt!  JSON error:\nAt line %s, column %s '
                          'the following error was encountered:\n%s', str(err.lineno),
                          str(err.colno), str(err.msg))
            return False
        except: # pylint: disable=bare-except
            logging.error('An unhandled execption occured while loading category data.')
            return False

        # If it's valid JSON, pass it to self.load_categories
        logging.debug('Loading category data from string: %s', json_string)
        return self.load_categories(json_data, append)

    def load_categories_from_file(self, file_path, append=False):
        '''
        Loads categories from JSON data in a file.  This validates against known schemas to ensure
        the data structure is correct.

        Parameters
        ----------
        file_path : string
            Path to the file to load.

        append : bool
            Whether this should replace all known categories or be added to them.

        Returns
        -------
        bool
            True if load succesful, False otherwise.
        '''
        # If loading something without JSON extension, may be fine, but bad practice, so warn.
        if file_path[-5:] != '.json':
            logging.warning('Loading a category file with the wrong file extension: %s  While not '
                            'strictly necessary, the extension should be ".json".', file_path)
        # Try to open the file and parse it as JSON or fail with message
        try:
            category_file = open(file_path, 'r')
            json_data = json.load(category_file)
            category_file.close()
        except IOError:
            logging.error('Could not open category file at: %s', file_path)
            sys.exit()
        except json.decoder.JSONDecodeError as err:
            logging.error('Category file is wholly corrupt!  JSON error:\nAt line %s, column %s '
                          'the following error was encountered:\n%s', str(err.lineno),
                          str(err.colno), str(err.msg))
            sys.exit()
        except: # pylint: disable=bare-except
            logging.error('An unhandled execption occured while loading a category file.')
            sys.exit()

        # If it's valid JSON, pass it to self.load_categories
        logging.debug('Loading category data from: %s', file_path)
        return self.load_categories(json_data, append)
