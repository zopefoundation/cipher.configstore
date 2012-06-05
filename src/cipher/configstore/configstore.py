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
"""Configuration Store
"""
from __future__ import absolute_import

import datetime
import dateutil.parser
import logging
import odict
import os
import ConfigParser
import zope.component
import zope.event
import zope.interface
import zope.lifecycleevent
import zope.schema
from zope.security.proxy import removeSecurityProxy

from cipher.configstore import interfaces

log = logging.getLogger(__name__)

novalue = object()

def stringify(s):
    if s is None:
        return ''
    return unicode(s)

def parse_time(s):
    return dateutil.parser.parse(s).time()


class ConfigurationStore(object):
    zope.interface.implements(interfaces.IConfigurationStore)
    listValueSeparator = ', '

    schema = None
    fields = None
    section = None

    def __init__(self, context, schema=None, section=None):
        if self.schema is None:
            self.schema = schema or zope.component.adaptedBy(self.__class__)[0]
        if self.section is None:
            self.section = section or self.schema.getName()
        self.context = self._getContext(context)

    def _getContext(self, context):
        return self.schema(context)

    def load_type_Time(self, unicode, field):
        return parse_time(unicode) if unicode else None

    def load_type_Timedelta(self, unicode, field):
        if not unicode:
            return
        h, m , s = [int(p) for p in unicode.strip().split(':')]
        return datetime.timedelta(seconds=h*3600+m*60+s)

    def load_type_Text(self, value, field):
        return value.replace('\n<BLANKLINE>\n', '\n\n')

    def load_type_Choice(self, unicode, field):
        if not unicode.strip():
            return None
        bound_field = field.bind(self.context)
        return bound_field.vocabulary.getTermByToken(unicode).value

    def load_type_List(self, unicode, field):
        if not unicode.strip():
            return []
        return [item.strip() for item in unicode.split(self.listValueSeparator)]

    def load_type_Tuple(self, unicode, field):
        return tuple(self.load_type_List(unicode, field))

    def load_type_Set(self, unicode, field):
        return set(self.load_type_List(unicode, field))

    def _load_field(self, name, field, config, context=None):
        if context is None:
            context = self.context
        if field.readonly:
            # skip read-only fields, especially __name__
            return False
        field_type = field.__class__
        if hasattr(self, 'load_'+name):
            converter = getattr(self, 'load_'+name, None)
        elif hasattr(self, 'load_type_'+field_type.__name__):
            converter = getattr(self, 'load_type_'+field_type.__name__, None)
            converter = lambda v, converter=converter: converter(v, field)
        elif zope.schema.interfaces.IFromUnicode.providedBy(field):
            converter = field.bind(context).fromUnicode
        else:
            # If we do not have a converter then it is probably meant to be.
            return False
        try:
            value = converter(
                unicode(config.get(self.section, name), 'UTF-8'))
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError,
                zope.schema.ValidationError, ValueError):
            # Ignore fields that fail validation, since the field might
            # simply not be set and no value is an invalid value.
            return False
        if value != getattr(context, name):
            try:
                setattr(context, name, value)
            except zope.schema.ValidationError, e:
                log.warn("Field %r %s failed validation: %s", context, name, e)
                # Ignore fields that fail validation, since the field might
                # simply not be set and no value is an invalid value.
                return False
            return True
        return False

    def _load(self, config):
        changed_fields = []
        for name, field in zope.schema.getFieldsInOrder(self.schema):
            __traceback_info__ = name
            if self.fields is None or name in self.fields:
                changed = self._load_field(name, field, config)
                if changed:
                    changed_fields.append(name)
        return changed_fields

    def load(self, config):
        changed_fields = self._load(config)
        stores = zope.component.subscribers(
            (self.context,), interfaces.IConfigurationStore)
        for store in stores:
            if not isinstance(store, self.__class__):
                store.load(config)
        zope.event.notify(
            interfaces.ObjectConfigurationLoadedEvent(
                self.context,
                zope.lifecycleevent.Attributes(self.schema, *changed_fields)
            ))

    def dump_type_Time(self, value, field):
        return value.strftime('%H:%M') if value is not None else ''

    def dump_type_Timedelta(self, value, field):
        return str(value) if value is not None else ''

    def dump_type_Text(self, value, field):
        if not value:
            return ''
        value = value.replace('\r\n', '\n')
        return value.replace('\n\n', '\n<BLANKLINE>\n')

    def dump_type_Choice(self, value, field):
        if value is None or value == '':
            return ''
        bound_field = field.bind(self.context)
        return bound_field.vocabulary.getTerm(value).token

    def dump_type_Tuple(self, value, field):
        return self.listValueSeparator.join(value) if value else ''

    dump_type_List = dump_type_Tuple
    dump_type_Set = dump_type_Tuple

    def _dump_field(self, name, field, config, value=novalue):
        __traceback_info__ = (name, field)
        if field.readonly:
            # skip read-only fields, we won't be loading them
            return
        field_type = field.__class__
        if hasattr(self, 'dump_'+name):
            converter = getattr(self, 'dump_'+name)
        elif hasattr(self, 'dump_type_'+field_type.__name__):
            converter = getattr(self, 'dump_type_'+field_type.__name__)
            converter = lambda v, converter=converter: converter(v, field)
        elif zope.schema.interfaces.IFromUnicode.providedBy(field):
            converter = stringify
        else:
            # It is not meant to be.
            return
        if value is novalue:
            value = getattr(self.context, name)
        unicode_value = converter(value)
        assert unicode_value is not None, "%r wasn't supposed to return None!" % converter
        config.set(self.section, name, unicode_value.encode('UTF-8'))

    def _dump(self, config):
        """Hook for custom config stores."""
        config.add_section(self.section)
        for name, field in zope.schema.getFieldsInOrder(self.schema):
            if self.fields is None or name in self.fields:
                self._dump_field(name, field, config)

    def dump(self, config=None):
        if config is None:
            config = ConfigParser.RawConfigParser(dict_type=odict.odict)
            config.optionxform = str # don't lowercase
        # Write object's configuration.
        self._dump(config)
        # Write any sub-object configuration.
        stores = zope.component.subscribers(
            (self.context,), interfaces.IConfigurationStore)
        for store in stores:
            __traceback_info__ = repr(store)
            store.dump(config)
        return config

class CollectionConfigurationStore(ConfigurationStore):
    section_prefix = None
    item_factory = None

    def _getContext(self, context):
        return self.schema(context)

    def _getItems(self):
        return self.context.items()

    def _getItemFactory(self, config, section):
        return self.item_factory

    def _add(self, name, item):
        self.context[name] = item
        # In case we are not dealing with a traditional container, let's set
        # the parent and name.
        # Note: I have honestly no idea why I originally even put this in.
        if hasattr(item, '__parent__') and item.__parent__ is None:
            item.__parent__ = removeSecurityProxy(self.context)
        if hasattr(item, '__name__') and item.__name__ is None:
            item.__name__ = name

    def _applyPostAddConfig(self, item, config, section):
        pass

    def load(self, config):
        # Remove all existing items
        removeSecurityProxy(self.context).__init__()
        # Load one item at a time.
        for section in config.sections():
            if not section.startswith(self.section_prefix):
                continue
            name = section[len(self.section_prefix):].decode('UTF-8')
            itemFactory = self._getItemFactory(config, section)
            __traceback_info__ = (section, itemFactory)
            item = itemFactory()
            item_store = interfaces.IConfigurationStore(item)
            item_store.section = section
            item_store.load(config)
            # Note sends a ContainerModifiedEvent which would causes a config
            # dump, overwriting the original file with partial information.
            # That's why we have this _v_load_in_progress "lock".
            self._add(name,  item)
            self._applyPostAddConfig(item, config, section)
        zope.event.notify(
            interfaces.ObjectConfigurationLoadedEvent(self.context))

    def dump(self, config=None):
        if config is None:
            config = ConfigParser.RawConfigParser(dict_type=odict.odict)
            config.optionxform = str # don't lowercase
        for name, item in self._getItems():
            if getattr(item, '__parent__', self) is None:
                # Sad story: you remove an item from a BTreeContainer
                # it emits ContainerModifiedEvent before deleting that item
                # (but after setting the item's __parent__ to None)
                # so if you've a subscriber for ObjectModifiedEvent that
                # dumps configuration after changes, you need to explicitly
                # filter out items that are about to be deleted.
                # See https://bugs.launchpad.net/bugs/705600
                continue
            item_store = interfaces.IConfigurationStore(item)
            item_store.section = self.section_prefix + name.encode('UTF-8')
            __traceback_info__ = item_store.section
            item_store.dump(config)
        return config

def createConfigurationStore(schema, section=None):
    return type(
        schema.getName()[1:]+'Store', (ConfigurationStore,),
        {'section': section, 'schema': schema})


class ExternalConfigurationStore(ConfigurationStore):

    def get_config_dir(self):
        return None

    def get_site(self):
        return None

    def get_filename(self):
        return self.context.__name__+'.ini'

    def _load_from_external(self, config):
        # Load general attributes.
        orig_section = self.section
        self.section = 'general'
        changed_fields = self._load(config)
        self.section = orig_section
        # Load other components.
        stores = zope.component.subscribers(
            (self.context,), interfaces.IConfigurationStore)
        for store in stores:
            if not isinstance(store, self.__class__):
                store.load(config)
        zope.event.notify(
            interfaces.ObjectConfigurationLoadedEvent(
                self.context,
                zope.lifecycleevent.Attributes(self.schema, *changed_fields)
            ))

    def load(self, config):
        fn = os.path.join(
            self.get_config_dir(), config.get(self.section, 'config-path'))
        __traceback_info__ = fn
        ext_config = ConfigParser.RawConfigParser(dict_type=odict.odict)
        ext_config.optionxform = str # don't lowercase
        ext_config.read(fn)
        self._load_from_external(ext_config)

    def _dump_to_external(self):
        # Compute the filename.
        cs = self.get_site()
        fn = os.path.join(
            self.get_config_dir(), cs.__name__, self.get_filename())
        # Create a new configuration for the table-specific API.
        config = ConfigParser.RawConfigParser(dict_type=odict.odict)
        config.optionxform = str # don't lowercase
        # Write object's configuration.
        orig_section = self.section
        self.section = 'general'
        __traceback_info__ = fn
        self._dump(config)
        self.section = orig_section
        # Write any sub-object configuration.
        stores = zope.component.subscribers(
            (self.context,), interfaces.IConfigurationStore)
        for store in stores:
            __traceback_info__ = (fn, store)
            store.dump(config)
        # Write the configuration out.
        with open(fn, 'w') as file:
            config.write(file)
        return fn

    def dump(self, config=None):
        if config is None:
            config = ConfigParser.RawConfigParser(dict_type=odict.odict)
            config.optionxform = str # don't lowercase
        # Write any sub-object configuration into a separate configuration file.
        fn = self._dump_to_external()
        # Just a small stub in the main config.
        config.add_section(self.section)
        config.set(
            self.section, 'config-path',
            os.path.relpath(fn, self.get_config_dir()))
        # Write a minimal configuration.
        return config
