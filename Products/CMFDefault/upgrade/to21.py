##############################################################################
#
# Copyright (c) 2008 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Upgrade steps to CMFDefault 2.1.

$Id$
"""
import logging

from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from five.localsitemanager import find_next_sitemanager
from five.localsitemanager.registry import FiveVerifyingAdapterLookup
from five.localsitemanager.registry import PersistentComponents
from zope.component import getMultiAdapter
from zope.component.globalregistry import base
from zope.component.interfaces import ComponentLookupError

from Products.GenericSetup.context import SetupEnviron
from Products.GenericSetup.interfaces import IBody

_XML = """\
<?xml version="1.0"?>
<componentregistry>
 <adapters/>
 <utilities>
  <utility interface="Products.CMFCore.interfaces.IDiscussionTool"
     object="portal_discussion"/>
  <utility interface="Products.CMFCore.interfaces.IMetadataTool"
     object="portal_metadata"/>
  <utility interface="Products.CMFCore.interfaces.IPropertiesTool"
     object="portal_properties"/>
  <utility interface="Products.CMFCore.interfaces.ISiteRoot" object=""/>
  <utility interface="Products.CMFCore.interfaces.ISyndicationTool"
     object="portal_syndication"/>
  <utility interface="Products.CMFCore.interfaces.IUndoTool"
     object="portal_undo"/>
  <utility interface="Products.GenericSetup.interfaces.ISetupTool"
     object="portal_setup"/>
  <utility interface="Products.MailHost.interfaces.IMailHost"
     object="MailHost"/>
 </utilities>
</componentregistry>
"""

def upgrade_default(tool):
    """2.0.x to 2.1.0 upgrade step handler
    """
    portal = aq_parent(aq_inner(tool))
    logger = logging.getLogger('GenericSetup.upgrade')
    upgrade_CMFSite_object(aq_base(portal), logger)
    upgrade_TypeInfos(portal, logger)

def upgrade_CMFSite_object(portal, logger):
    try:
        components = portal.getSiteManager()
    except ComponentLookupError:
        next = find_next_sitemanager(portal)
        if next is None:
            next = base
        name = '/'.join(portal.getPhysicalPath())
        components = PersistentComponents(name, (next,))
        components.__parent__ = portal
        portal.setSiteManager(components)
        logger.info("Site manager '%s' added." % name)
    else:
        if components.utilities.LookupClass != FiveVerifyingAdapterLookup:
            # for CMF 2.1 beta instances
            components.__parent__ = portal
            components.utilities.LookupClass = FiveVerifyingAdapterLookup
            components.utilities._createLookup()
            components.utilities.__parent__ = components
            logger.info('LookupClass replaced.')
    if not tuple(components.registeredUtilities()):
        getMultiAdapter((components, SetupEnviron()), IBody).body = _XML
        logger.info('Utility registrations added.')

    if not portal.hasProperty('email_charset'):
        portal.manage_addProperty('email_charset', 'iso-8859-1', 'string')
        prop_map = list(portal._properties)
        for i in range(len(prop_map)):
            if prop_map[i]['id'] == 'default_charset':
                email_charset_info = prop_map.pop(-1)
                prop_map.insert(i+1, email_charset_info)
                portal._properties = tuple(prop_map)
                break
        logger.info("'email_charset' property added.")

_FACTORIES = {
    'CMFCore-manage_addPortalFolder': 'cmf.folder',
    'CMFCore-manage_addCMFBTreeFolder': 'cmf.folder.btree',
    'CMFDefault-addDocument': 'cmf.document',
    'CMFDefault-addFavorite': 'cmf.favorite',
    'CMFDefault-addFile': 'cmf.file',
    'CMFDefault-addImage': 'cmf.image',
    'CMFDefault-addLink': 'cmf.link',
    'CMFDefault-addNewsItem': 'cmf.newsitem'}

def upgrade_TypeInfos(portal, logger):
    ttool = portal.portal_types
    for ti in ttool.listTypeInfo():
        key = '%s-%s' % (ti.getProperty('product'), ti.getProperty('factory'))
        if key in _FACTORIES:
            ti._updateProperty('product', '')
            ti._updateProperty('factory', _FACTORIES[key])
            logger.info("TypeInfo '%s' changed." % ti.getId())
