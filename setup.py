import os
import re

from setuptools import setup

# Avoid polluting the .tar.gz with ._* files under Mac OS X
os.putenv('COPYFILE_DISABLE', 'true')

# Prevent distutils from complaining that a standard file wasn't found
README = os.path.join(os.path.dirname(__file__), 'README')
if not os.path.exists(README):
    os.symlink(README + '.md', README)

VERSION = os.path.join(os.path.dirname(__file__), 'userlog', '__init__.py')
with open(VERSION) as f:
    version = re.search("^__version__ = '(.*)'$", f.read(), re.M).group(1)

description = "Logs users' recent browsing history."

with open(README) as f:
    long_description = '\n\n'.join(f.read().split('\n\n')[2:4])

setup(
    name='django-userlog',
    version=version,

    description=description,
    long_description=long_description,

    url='https://github.com/aaugustin/django-userlog',

    author='Aymeric Augustin',
    author_email='aymeric.augustin@m4x.org',

    license='BSD',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    packages=['userlog'],

    package_data={
        'userlog': [
            'locale/*/LC_MESSAGES/*',
            'templates/userlog/*',
            'static/userlog/*/*',
        ],
    },
)
