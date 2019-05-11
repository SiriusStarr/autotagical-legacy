import doctest


def run_tests(module):
    print('Testing ' + module + ' module:')
    return doctest.testfile(module)
