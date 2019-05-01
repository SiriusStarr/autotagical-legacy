import os
import setuptools
from autotagical import __version__ as version
from tests.tests import run_tests
from setuptools.command.test import test

class Doctest(test):
    def run(self):
        results = run_tests('categories')
        if results.failed:
            raise Exception(results)
        print('Okay!')
        results = run_tests('filtering')
        if results.failed:
            raise Exception(results)
        print('Okay!')
        results = run_tests('schema')
        if results.failed:
            raise Exception(results)
        print('Okay!')
        results = run_tests('moving')
        if results.failed:
            raise Exception(results)
        print('Okay!')
        results = run_tests('naming')
        if results.failed:
            raise Exception(results)
        print('Okay!')
        results = run_tests('file_handler')
        if results.failed:
            raise Exception(results)
        print('Okay!')
        super().run()
        print('All tests passed!')

# Utility function to read the README file.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setuptools.setup(
    name="autotagical",
    version=version,
    author="SiriusStarr",
    author_email="2049163+SiriusStarr@users.noreply.github.com",
    description=("A utility to automagically rename and sort tagged files (such as those produced "
                 "by TagSpaces) according to user-defined schemas."),
    license="GPLv3",
    keywords="file sort tag rename tagging tagspaces",
    url="https://github.com/SiriusStarr/autotagical",
    packages=['autotagical'],
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    cmdclass={'test': Doctest},
    scripts=['bin/autotagical'],
    install_requires=[
        'setuptools',
        'jsonschema>=3',
        'packaging'
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
    ],
    include_package_data=True
)
