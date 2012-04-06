"""Tests"""
import doctest
import unittest


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite(
            "configstore.txt",
            optionflags=doctest.NORMALIZE_WHITESPACE|
                        doctest.ELLIPSIS|
                        doctest.REPORT_ONLY_FIRST_FAILURE
                        #|doctest.REPORT_NDIFF
            ),
        ))
