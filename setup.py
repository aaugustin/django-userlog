from __future__ import unicode_literals

import codecs
import os.path
import re

import setuptools

root_dir = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(root_dir, 'userlog', '__init__.py'), encoding='utf-8') as f:
    version = re.search("^__version__ = '(.*)'$", f.read(), re.M).group(1)

description = "Logs users' recent browsing history."

with codecs.open(os.path.join(root_dir, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
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
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
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
    packages=[
        'userlog',
    ],
    package_data={
        'userlog': [
            'locale/*/LC_MESSAGES/*',
            'templates/userlog/*',
            'static/userlog/*/*',
        ],
    },
)
