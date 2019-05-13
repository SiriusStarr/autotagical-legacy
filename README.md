# autotagical

*autotagical* is a utility to automagically rename and sort tagged files (such
as those produced by [TagSpaces](https://github.com/tagspaces/tagspaces))
according to user-defined schemas.  It reads in tagged files from one of more
input directories then renames and/or moves them to an output folder hierarchy
according to rules specified in user-provided schemas.  It is intended for use
in concert with file tagging software, e.g.
[TagSpaces](https://github.com/tagspaces/tagspaces).

## Getting Started/Installation

*autotagical* may be most easily installed with *pip* by running:

```bash
pip install autotagical
```

If you'd like to run *autotagical* by cloning this repository, then you'll need
to install the following requirements, e.g. with *pip*:

* `setuptools`
* `jsonschema>=3`
* `packaging`

## Using autotagical

### Usage

```bash
autotagical [-h] [-V] [-C <config file>] [-H] [-i <input path>]
            [-I <ignore file>] [-R] [-o <output path>] [-O]
            [-g <tag group file>] [-s <schema file>] [-A] [--cleanin]
            [--cleanout] [-c] [-F] [-k] [-m] [-M] [-n] [-N] [-t]
            [--debug] [-l <log file>] [-L] [-P] [-q] [-v] [--force]
            [--yes]
```

### Help Options

These options display helpful information and exit.

* `[-h/--help]` -- Display a help/usage message and exit.
* `[-V/--version]` -- Display the current version and information about known
  file formats and exit.

### Configuration Options

* `[-C/--config <config file>]` -- Loads the config file at the specified path.

### Input Options

These options determine behavior loading in files to be moved and/or renamed.
At least one input folder must be specified.

* `[-H/--hidden]` -- Process hidden files (and directories, if -R is specified).
* `[-i/--input <input folder>]` -- Path to a folder with input files.  May be
  specified more than once.
* `[-I/--ignore <ignore file>]` -- Path to file patterns (regex format) to
  ignore (each on new line).  May be specified more than once.
* `[-R/--recursive]` -- Load files recursively from input folders, i.e. descend
  into subfolders.

### Output Options

These options determine behavior in outputting move/renamed files (but do not
specify the rules by which they are to be moved and/or renamed).  At least one
output folder must be specified (by one option or the other).

* `[-o/--output]` -- Path to a root folder to output files to.  May be specified
  more than once (output will be duplicated to each).
* `[-O/--organize]` -- Organize files in place (i.e. use the first input folder
  for output).  Often used with -R.

### Schema Options
These options specify the rules for moving/renaming files and are the heart of
*autotagical*.  Information on the structure of these files may be found below
in the [Tag Group Format](#tag-group-format) and
[Schema Format](#schema-format) sections.

* `[-g/--groups <tag group file>]` -- Path to a file to read tag groups from.
  May be specified more than once (groups will be combined).  Files may be in
  either the *[TagSpaces](https://github.com/tagspaces/tagspaces)* or the
  *autotagical* format.
* `[-s/--schema <schema file>]` -- Path to a schema file to move/rename files
  based on.  May be specified more than once, in which case rules are
  prioritized in the order files are specified.

### Functionality Options

These options tweak the default functioning of *autotagical* as specified
below, typically adjusting how various circumstances are dealt with.

* `[-A/--allmatchroot]` --  Makes the root of an output folder match all tags,
  i.e. every single file will be moved to the output folder, even if it does not
  match anywhere more specifically.  Use of this option is bad practice
  (consider using the `/*|` operator as a root filter instead), but it is
  provided for the user's convenience.  This option does **not** imply `-M`,
  i.e. files that could not be renamed will not be moved to the root folder
  just because `-A` is set.
* `[--cleanin]` -- Clean up (delete) all empty folders in the input folder/s.
  This *will* recurse, whether or not the `-R` flag is set.
* `[--cleanout]` -- Clean up (delete) all empty folders in the output folder.
  This *will* recurse, whether or not the `-R` flag is set.
* `[-c/--clean]` -- Clean up (delete) all empty folders in both input and output
  folders.
* `[-F/--failforcerename]` -- This option flags failing to rename a
  manually-named file that is being forcibly renamed due to the `-N` option
  should be considered a failure to name the file.  That sounds complicated, but
  consider these cases:
  * `[-F]` -- Normal behavior (option will be ignored).
  * `[-N]` -- Force rename manually-named files, but manual names are "good
  enough" and manually-named files that cannot be renamed will be moved.
  * `[-F -N]` -- Force rename manually-named files and treat failures as
  failures.  Manually-named files that cannot be renamed will **not** be moved.
  * `[-N -M]` -- Force rename manually-named files.  All files will be moved.
  * `[-F -N -M]` -- Equivalent to `-N -M`.  `-F` has no effect.
* `[-k/--keep]` -- Keep original files in the input folders untouched, i.e copy
  files to their new destinations rather than move them.
* `[-m/--move]` -- Only move files into a directory structure, do not try to
  rename them.
* `[-M/--moveall]` -- Move all files, not only ones that are manually-named/
  successfully renamed.
* `[-n/--name]` -- Only rename files, do not try to move them into any directory
  structure.  All files will be placed in the root of the output folder.
* `[-N/--renamemanual]` -- Forcibly try to rename manually-named files, not just
  unnamed ones.
* `[-t/--trial]` -- Trial run.  Do not actually move or rename files, just log
  what would happen.  Combine with `-v` to check output before live run.
  **Using this is good practice,** especially after making any changes to a
  schema or options.  The `-t` option ensures no changes will be reflected to
  disk whatsoever.

### Logging Options

These options tweak what sorts of messages are displayed when *autotagical* is
run (and whether to save them or just print them to the console).

* `[--debug]` -- Display absolutely everything.  You should probably never use
  this.
* `[-l/--log <log file>]` -- Output messages to the specified file rather than
  just the console.  By default, messages will be appended to the end of the
  file.
* `[-L/--overwritelog]` -- Overwrite the specified log file, rather than append
  to it.  Has no effect without `-l`.
* `[-P/--posix]` -- Silence warnings specific to Windows.  Use this **only** if
  the files are never to be used with Windows systems (which are pickier about
  what file names can contain).
* `[-q/--quiet]` -- Silence all warnings and only display actual errors.  Use of
  this is **not recommended,** as warnings are typically printed for good
  reason.
* `[-v/--verbose]` -- Print all actions taken.  This will list every file
  movement/renaming, rather than merely warning about failures.  Most useful
  when combined with `-t` to check that a schema is doing what one wants before
  running it for real.

### Unsafe Options

Do not use these unless you have very good reason to.  **Data loss can occur.**

* `[--force]` -- Forcibly move/rename files, even if there is a file or
  directory in the way.  **This will clobber files;** use at your own risk, as
  data loss can occur.
* `[--yes]` -- Assume "yes" for all user prompts.  This implies `--force` and
  **will clobber files and directories.**  Use at your own risk, as data loss
  can occur.

### Setting Priority

*autotagical* will always preferentially use settings specified in the
following order, from highest to lowest, with each overriding any settings from
lower priority sources.  Note that only **one** config file will be loaded (the
first by priority).

1. Command-line arguments.
1. Config file (first found from below).
  1. Config file loaded using `-C/--config` argument.
  1. `.autotagrc` file in output folder (first folder containing one is used).
  1. `.autotagrc` file in input folder (first folder containing one is used).
  1. `.autotagrc` file in `autotagical` module folder.

### Config File Format
`.autotagrc` (or any config file specified via command-line) should have the
same format as any command line arguments one would otherwise care to pass.
**Unsafe options will be ignored in config files,** i.e. `--force` and `--yes`
will have no effect if set in a config file.  This is to prevent data loss
without explicit user input.  Whitespace and newlines are ignored, e.g. one
might write:

```bash
-H

  -P
```

in a config file to process hidden and ignore Windows-specific warnings.

## Tag Group Format

*autotagical* is capable of reading the JSON files produced by exporting tag
groups from [TagSpaces](https://github.com/tagspaces/tagspaces).  Alternately,
tag groups may be defined in a more simple, somewhat more human-readable
fashion in JSON.  This *autotagical* tag group format supports additional
features not available in the TagSpaces format, detailed below.

```json
{
  "file_type": "autotagical_tag_groups",
  "tag_group_file_version": "1.1",
  "tag_groups": [
    {
      "name": "tag group 1",
      "tags": ["tag1", "tag2"...]
    },
    {
      "name": "tag group 2",
      "tags": ["tag3", "/G|tag group 1", "/RE|regex 1",...]
    },
  ]
}
```

### Inheritance

In the *autotagical* format, tag groups support simple inheritance, where a
child tag group may be defined in terms of one or more parent tag groups (as
well as any additional tags).  Inheritance is indicated by prefixing a group
name with `/G|` in the `tags` property of a group.  In such cases, the child
group will inherit all tags in any of the parent groups.  This is useful for
simplicity; it ensures that one only has to manually define the most "leaf" tag
groups while still writing filters based on more broad groups, all of which
will update if the more refined groups are updated.  Consider the following
simple use case:

```json
{
    "file_type": "autotagical_tag_groups",
    "tag_group_file_version": "1.1",
    "tag_groups": [
        {
            "name": "American Styles",
            "tags": [
                "ipa",
                "dipa",
                "pale_ale"
            ]
        },
        {
            "name": "Belgian Styles",
            "tags": [
                "witbier",
                "dubbel",
                "tripel"
            ]
        },
        {
            "name": "Beer",
            "tags": [
                "/G|American Styles",
                "/G|Belgian Styles"
            ]
        }
    ]
}
```

Here, we have defined the `Beer` group in terms of `American Styles` and
`Belgian Styles`, rather than having to specify all 6 tags that should fall
under it.  Not only is this quicker to write, but it prevents errors of
oversight when one decides to add tags later.  If, for example, `quadrupel`
is added to the `Belgian Styles` group, it will be part of the `Beer` group
without one having to remember to manually add it in two places.  While this
simple case doesn't seem that unmanageable without inheritance, the number of
places where duplicate tags have to be added can quickly spiral out of control
with multiple levels of tag group.

Keep in mind the following details about inheritance:
*  **Multiple inheritance** -- Tag groups can inherit from multiple parent
   group (as shown in the example).
*  **Multilevel inheritance** -- Tag groups support multilevel inheritance,
   i.e. an `Alcohol` group might inherit from `Beer` which inherits from
   `American Styles`.
*  **The (lack of) diamond problem**  -- As there is no overriding in tag group
   inheritance, the diamond problem (where a grandparent is inherited via two
   different routes) is handled without problem.
*  **Circular inheritance** -- It is okay for two groups to inherit from each
   other (whether via intermediaries or not).  Each inheritance path will
   only be followed once, i.e. a tag group will stop "following" an
   inheritance path if it is instructed to inherit from itself.
*  **Flexible ordering** -- Tag group inheritance is flexible in the order that
   groups are defined.  There is no need for a tag group to be located after
   a group it inherits from.  In fact, tag groups can inherit from groups in
   completely different tag group files, regardless of the order they are loaded
   in (so long as they are both loaded).

### Regex Tag Groups

The *autotagical* tag group format supports defining tag groups in terms of
regexes.  This can be incredibly powerful in certain situations.  For example,
consider tagged bank statements.  Rather than having to manually add every
account number tag to an "Account Number" group, one can instead define a tag
group as follows:

```json
{
    "name": "Account Number",
    "tags": ["/RE|(?:xx|\\*\\*)[0-9]{4}"]
}

```

This will make any tag of the form `**1234` or `xx1234` match the "Account
Number" tag group.  If one deals with a large number of tags with a standardized
form, this can be extremely valuable, especially if they change frequently.

Keep in mind the following details about regex tag groups:
*  **Full match** -- Regexes are used with `re.fullmatch()` and as such must
   match 100% of the tag name.
*  **Inheritance** -- Regexes will be inherited as with any other tags in a
group.
*  **Mixed and matched** -- A tag group can be defined in terms of any
   combination of inheritance, normal tags, or regexes.  They do not need to be
   specified solely in terms of regexes.
*  **Tag in group (/?TIG|) operator** -- Regex tag groups work normally with
   the tag in group format string operator.  The first tag to match the regex
   will be returned for it.

## Schema Format

A schema is defined in a human-readable fashion in JSON and should consist of a
single object as follows:

```json
{
  "file_type": "autotagical_schema",
  "schema_file_version": "1.1",
  "tag_formats": [],
  "unnamed_patterns": [],
  "renaming_schemas": [],
  "movement_schema": []
}
```

Each of these four keys should be assigned to an array, the structure of which
is described in the following sections.

### tag_formats

```json
"tag_formats": [
  {
    "tag_pattern": "Regex containing groups: file, raw_tags, tags, and extension.",
    "tag_split_pattern": "Regex to split tags with"
  },
  ...
]

```

The various patterns must be valid Python regexes.  "tag_pattern" will be used
with `re.fullmatch()` and should match the entirety of a file name and contain
the following named groups:

* `file` -- Matches the original file name (without tags and extension).
* `raw_tags` -- Matches the entirety of tag data to be preserved, including any
delimeters/demarcating characters.
* `tags` -- Matches only the tags themselves and any separating characters.
* `extension` -- Matches the file extension (if any).

"tag_split_pattern" should match whatever delimiter separates individual tags
and will be used with `re.split()`.  An example is provided below, which
matches the tag format used by
[TagSpaces](https://github.com/tagspaces/tagspaces):

```json
"tag_formats": [
  {
    "tag_pattern": "(?P<file>.+)(?P<raw_tags>\\[(?P<tags>.+?)\\])(?P<extension>.*?)",
    "tag_split_pattern": "\\s+"
  }
]
```

More than one such set of patterns may be provided in a single `tag_formats`
array, allowing *autotagical* to deal with files tagged in multiple formats in
one run.

### unnamed_patterns

```json
"unnamed_patterns": [
  "regex pattern 1",
  "regex pattern 2",
  ...
]
```

The various patterns must be valid Python regexes.  Each will be used with
`re.match()` and should match the file names (less tags) of such files to be
treated as requiring renaming.  They will be matched against the concatenation
of the `file` and `extension` groups produced by the use of "tag_pattern"
above, so do not attempt to match against anything not captured by those two
groups.  An example is provided below, which might match PDF files with
timestamps produced by two different scanners:

```json
"unnamed_patterns": [
  "[0-9]{4}_[0-9]{2}_[0-9]{2}_[0-9]{2}_[0-9]{2}_[0-9]{2}\\s*.pdf",
  "(Pages\\sfrom)?\\s*XScan_[0-9]{14}\\s*.pdf"
]
```

### renaming_schema

```json
"renaming_schemas": [
  {
    "filter": ["condition 1", "condition 2", ...],
    "format_string": "file name format string"
  },
  ...
]
```

"renaming_schemas" is simply a list of filters and an explanation of how to
name files matching any of them.  This list is ordered, and files will be
renamed according to the first they match, e.g. if a file has `tag1` and `tag2`
and the first filter in the array matches `tag2` and the second `tag1`, the
file will be renamed according to `tag2`.  This allows one to define priorities
of renaming.  See the [Filters](#filters) section for information on filters,
conditions, and the various operators one may include in them.

"format_string" defines how to rename files matching the filter.  It cannot
contain the `/` character except where it denotes operators (as
file names cannot contain `/`).  At its simplest, it is simply a string that
the file will be renamed to, but that string may include any number/combination
of operators.  See the [Format Strings](#format-strings) section for
information on format strings and the various operators one may include in them.

### movement_schema

```json
"movement_schema": [
  {
    "filter": ["condition 1", "condition 2", ...],
    "subfolder": "<format string 1>",
    "sublevels": [
      {
        "filter": ["condition 3", "condition 4", ...],
        "subfolder": "<format string 2>",
        "sublevels": [...]
      },
      ...
    ]
  },
  ...
]
```

"movement_schema" defines an output folder hierarchy iteratively by nesting
filters.  At each folder level, multiple filters can exist that either pass
files to lower subfolders or place them at the current level.  These lists are
ordered, and files will be sorted according to the first filter they match,
e.g. if a file has `tag1` and `tag2` and at a level the first filter in the
array matches `tag2` and the second `tag1`, the file will be sorted according
to `tag2`.  This allows one to define priorities of sorting.  See the
[Filters](#filters) section for information on filters, conditions, and the
various operators one may include in them.

If "subfolder" contains a format string, it will be interpreted and added to
the folder hierarchy that the file will be placed in (and further sorted based
on "sublevels"); if it is left blank `""`, files will be placed in the current
(in the hierarchy) directory without further sorting.  If "sublevels" is left
empty `[]`, files will be placed in the specified subfolder without further
sorting.  Note that a movement schema does not have to have a path for every
possible file.  Files that fail to "find a home" will be left in the input
folder and a warning will be printed (unless `-A` is specified).  See the
[Format Strings](#format-strings) section for information on format strings and
the various operators one may include in them.

Additionally, note that complete hierarchies (i.e. those that terminate with
explicitly placing the file in a folder) will be preferred over partial
hierarchies (i.e. if a file percolates some distance down a hierarchy and then
matches no filters).  In the event that no complete hierarchy can be found, the
first partial one *will* be used to move the file.  It is bad practice to rely
on this behavior though; one should use the `/*|` operator if one explicitly
wishes absolutely any file that reaches a filter level to reside there.

### Filters

A filter (wherever it might show up in a schema) is defined by an array of
condition sets.  These condition sets are combined in the logical sense by
*inclusive or*, i.e. matching at least one condition set is necessary and
sufficient to match the overall filter.  At their simplest, a condition set may
simply be a tag, e.g. `"filter": ["tag1", "tag2"]` will match any file with
either `tag1` or `tag2` (or both) on it.  However, the following operators may
be used to construct more complex condition sets (whether in filters or in the
conditional `/?|` operator):

* `/G|` -- The prefix `/G|` is used to denote a tag group instead of a tag
  name, e.g. `"filter": ["/G|Group 1", "tag2"]` will match any file with at
  least one tag in `Group 1` or the tag `tag2` (or both).
* `/*|` -- The all operator `/*|` matches all files, regardless of how they are
  tagged.
* `/&|` -- `/&|` is a logical "and" operator, requiring matching both
  conditions, e.g. `"filter": ["tag1/&|tag2"]` will match files that have *both*
  `tag1` and `tag2`.  A condition may contain any number of `/&|` operators,
  e.g. one may create the condition `"tag1/&|tag2/&|/G|Group 1"`.
* `/!|` -- The not prefix `/!|` negates the next condition.  **This prefix must
  come before any others logically,** i.e. you must write `/!|/G|<group>` rather
  than `/G|/!|<group>` or `/!|/*|` rather than `/*|/!|`.  The `/!|` operator
  *can* follow the logical "and" operator `/&|`, e.g. `"<tag1>/&|/!|<tag2>"`,
  which will match any file that has `tag1` and does not have `tag2`.

There are no (realistic) limits on the degree to which these operators may be
combined or how many condition sets a filter might have.

### Format Strings

A format string is simply a string that may or may not contain various
operators.  These operators will be replaced with the corresponding data when
the format string is interpreted.

* `/EXT|` -- Anywhere it is put in the format string, `/EXT|` will be replaced
  with the original extension of the file, as defined by the `extension` group
  in the "tag_formats" regex that matched the file.  This is obviously useful if
  you're renaming multiple types of file and want to preserve extensions.  You
  will almost always want to end your format string with `/EXT|`.
* `/FILE|` -- Anywhere it is put in the format string, `/FILE|` will be
  replaced with the original name of the file, as defined by the `file` group in
  the "tag_formats" regex that matched the file.
* `/TAGS|` -- Anywhere it is put in the format string, `/TAGS|` will be
  replaced with the tags on the original file.  **This is necessary to avoid
  your renamed files becoming de-tagged** and should almost always be included
  in a renaming format string.
* `/?|<condition>/T|<true text>/F|<false text>/E?|` -- The conditional operator
  `/?|` allows for conditional naming.  If `<filter>` is matched, the entire
  expression will be replaced with `<true text>`; if it does not match, the
  entire expression will be replaced with `<false text>`.  Either text (or both,
  but why would you) may be empty.  The conditional operator can take anything
  that can be in a filter condition.  See the [Filters](#filters) section for
  information on filters, conditions, and the various operators one may include
  in them.  `<true text>` and `<false text>` may contain other operators, i.e.
  `/EXT|`, `/FILE|`, `/TAGS|`, and `/ITER|`.  Note: conditional operators
  **cannot** be nested or contain `/?T|<tag>/|` or `/?G|<tag group>/|` within
  replacement text.
* `/?T|<tag>/|` -- The tag conditional operator `/?T|` will insert the literal
  name of the tag `<tag>` if it is present on the file.  Note that this is
  equivalent to `/?|<tag>/T|/<tag>/F|/E?|`; it is merely a shortcut.
* `/?G|<tag group>/|` -- The tag group conditional operator `/?G|` will insert
  the literal name of the tag group `<tag group>` if one of its tags is present
  on the file.  Note that this is equivalent to `/?|/G|<tag group>/T|<tag
  group>/F|/E?|`; it is merely a shortcut.
* `/?TIG|<tag group>/|` -- The "tag in group" operator is a special operator
  that will insert a tag on the file that is in the specified tag group.  For
  example, `/?TIG|group1?/|` will resolve to `tag1` if `tag1` is on the file and
  in `group1`, or `tag2` if `tag2` is on the file and in `group1`.  If multiple
  tags on the file are in the group, the first (in tagging order, left-to-right)
  will be substituted in.  If the file lacks a tag in the group, the entire
  operator will simply be blank.  This "tag in group" operator is most useful
  for writing flexible schema where the exact tags cannot be predicted in
  advance.  For example, if one wanted to sort bank statements into folders
  based on what account they are associated with, one could use the "tag in
  group" operator with an "Account Number" group and then only have to update
  the tag group with the various account number tags, rather than having to
  specify every account number in the schema.  As an example, consider the
  following cases, with `Group 1 = tag1, tag3` and
  `format_string = "Tag: /?TIG|Group 1/|"`:
  * `File [tag1, tag2]` -- "Tag: tag1"
  * `File [tag2, tag4]` -- "Tag: "
  * `File [tag1, tag2, tag3]` -- "Tag: tag2"
* `/ITER|<text>/#|<other text>/EITER|` -- The `/ITER|` operator is complicated
  but important.  It is invoked only in the event that multiple files are going
  to be renamed to the same name.  In this case, the text is placed in the file
  name, along with `/#|` being replaced by the n-th file that this is that has
  had the same name.  Otherwise, the entirety of the `/ITER|` operator is
  ignored.  **The /ITER| operator should not be used in folder name format
  strings.  It will be ignored.**
  In essence, the `/ITER|` tag "counts" how many times the same file name has
  been produced.  It is good practice to always include an `/ITER|` operator in
  your schema to avoid files not being renamed due to potential clobbering.
  `/#|` may appear more than once in an `/ITER|` operator, but there is usually
  no need to.  The `/ITER|` operator *may* contain any other operator, including
  the conditional operator `/?|`, but may not be nested.  Note that the `/ITER|`
  operator **will not be used** if files end up with the **same name but
  different output directories**.  It will only appear if necessary to avoid
  clobbering.  An example will make this easier to understand.  Consider the
  format string `Widget/ITER| /#|/EITER|` in the following cases:
  * 1 matching file -- The file will be named `Widget`.
  * 3 matching files in same folder -- The files will be named `Widget 1`,
    `Widget 2`, and `Widget 3`.
  * 3 matching files, each in a different folder -- The files will all be named
    `Widget`.



## Known Issues

* Only POSIX hidden files are considered hidden, i.e. those that begin with a
`.` dot, not those hidden as Windows does it.  This is most likely a **Won’t
Fix**.


## Tests

`autotagical` may be tested by cloning this repository and running:

```bash
python setup.py test
```

from within the root directory.  Note that this may require `python3` instead
of `python`, depending on your *python* installation.


## Authors

* **SiriusStarr**

## License

This project is licensed under the GNU General Public License v3.0 - see the
[LICENSE.md](LICENSE.md) file for details
