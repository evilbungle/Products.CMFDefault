##parameters=
##
from ZTUtils import Batch
from ZTUtils import LazyFilter
from Products.CMFCore.utils import getUtilityByInterfaceName
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.utils import decode

utool = getToolByName(script, 'portal_url')
stool = getUtilityByInterfaceName('Products.CMFCore.interfaces.ISyndicationTool')


if not stool.isSyndicationAllowed(context):
    context.REQUEST.RESPONSE.redirect(context.absolute_url() +
             '/rssDisabled?portal_status_message=Syndication+is+Disabled')
    return

options = {}

syndication_info = stool.getSyndicationInfo(context)
converter = {'daily':1, 'weekly':7, 'monthly': 30, 'yearly': 365}
ttl = 60 * 24 * (syndication_info['frequency'] *
                    converter[syndication_info['period']]
                )

syndication_info.update({'description': context.Description(),
                         'title': context.Title(),
                         'url': context.absolute_url(),
                         'ttl': ttl,
                         'portal_url': utool()}
                        )
syndication_info['base'] = syndication_info['base'].rfc822()

options['channel_info'] = syndication_info

key, reverse = context.getDefaultSorting()
items = stool.getSyndicatableContent(context)
items = sequence.sort( items, ((key, 'cmp', reverse and 'desc' or 'asc'),) )
items = LazyFilter(items, skip='View')
b_size = stool.getMaxItems(context)
batch_obj = Batch(items, b_size, 0, orphan=0)
items = []
for item in batch_obj:
    items.append( { 'date': item.modified().rfc822(),
                    'description': item.Description(),
                    'listCreators': item.listCreators(),
                    'listSubjects': item.Subject(),
                    'publisher': item.Publisher(),
                    'rights': item.Rights(),
                    'title': item.Title(),
                    'url': item.absolute_url(),
                    'uid': None } )
options['listItemInfos'] = tuple(items)

return context.RSS_template(**decode(options, script))
