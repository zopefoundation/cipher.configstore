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
"""Tests"""
import doctest
import re
import sys
import unittest
from zope.testing import renormalizing

checker = renormalizing.RENormalizing([
    # Python 3 unicode removed the "u".
    (re.compile("u('.*?')"),
     r"\1"),
    (re.compile('u(".*?")'),
     r"\1"),
    # Python 3 changed set representation.
    (re.compile("set\(\[?(.*?)\]?\)"),
     r"{\1}"),
    # ConfigParser location change.
    (re.compile("ConfigParser.RawConfigParser"),
     r"configparser.RawConfigParser"),
    ])

def setUp(test):
    test.globs.update({
        'PY2': sys.version_info[0] == 2,
        })


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite(
            "configstore.txt",
            setUp=setUp,
            checker=checker,
            optionflags=doctest.NORMALIZE_WHITESPACE|
                        doctest.ELLIPSIS
            ),
        ))
