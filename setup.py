##############################################################################
#
# Copyright (c) Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Setup for package cipher.configstore
"""
import os
import sys
from setuptools import setup, find_packages

PY2 = sys.version_info[0] == 2

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name='cipher.configstore',
    version='2.0.0a2',
    url="http://pypi.python.org/pypi/cipher.configstore/",
    author='Zope Foundation and Contributors',
    author_email='zope-dev@zope.org',
    keywords="CipherHealth configuration storage configparser",
    long_description=(
        read('README.txt')
        + '\n\n' +
        read('CHANGES.txt')
        ),
    license='ZPL 2.1',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Framework :: Zope3'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    extras_require=dict(
        test=[
            'zope.testing',
            'z3c.coverage',
            'coverage',
            'python-subunit',
            'junitxml'],
    ),
    install_requires=[
        'python-dateutil',
        'setuptools',
        'zope.component',
        'zope.event',
        'zope.interface',
        'zope.lifecycleevent',
        'zope.schema',
        'zope.security',
    ] + (['odict'] if PY2 else []),
    tests_require=['zope.testing'],
    test_suite='cipher.configstore.tests.test_suite',
    include_package_data=True,
    zip_safe=False
    )
