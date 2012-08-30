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
"""Interfaces"""

import zope.interface
import zope.schema
from zope.lifecycleevent import ObjectModifiedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent


class ConfigurationLoadError(Exception):
    pass


class IConfigurationStore(zope.interface.Interface):
    """ConfigParser-based configuration store.

    The interface is meant to be used as an adapter of a given object.
    """

    schema = zope.interface.Attribute('The schema to be serialized.')

    section = zope.schema.ASCIILine(
        title=u'Section Name',
        description=u'The name of the section in the configuration.',
        required=True)

    def load(config):
        """Load configuration and apply it to the object."""

    def dump(config=None):
        """Dump the object's state into the configuration.

        If the `config` paramter is `None`, a configuration object is created.
        """


class ICipherObject(zope.interface.Interface):
    "mark all Cipher objects"


class ICipherConfigurationComponent(zope.interface.Interface):
    """A component serving as configuration for the Cipher application."""


class ICipherConfiguration(ICipherConfigurationComponent):
    """A sub-object that contains configuration for ICipherSite."""

    __parent__ = zope.interface.Attribute("ICipherSite")

    title = zope.interface.Attribute(u'The name of the configuration.')

    lastVerificationResult = zope.interface.Attribute(
        u"""The result object of the last verification.

        The attribute can be set to None signaling that no meaningful result
        is available. This can either be the case either after initialization
        or whenever some state of the configuration was changed.
        """)

    def verify():
        """Verify the configuration and return a verification result.

        A verification result is a map of metric checked and a tuple of status
        code and reason. HTTP status code conventions are used. For example::

          {'test1': (200, 'Ok'),
           'test2': (400, 'Failed to find somehting.')}
        """


class IObjectConfigurationLoadedEvent(IObjectModifiedEvent):
    """We've just loaded an object's configuration from disk."""


class ObjectConfigurationLoadedEvent(ObjectModifiedEvent):
    zope.interface.implements(IObjectConfigurationLoadedEvent)
