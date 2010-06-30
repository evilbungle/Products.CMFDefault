"""
Change user preferences
$Id$
"""

from zope.schema import Choice, Bool
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from zope.schema.interfaces import IVocabulary, IVocabularyFactory
from zope.interface import Interface, directlyProvides, alsoProvides
from zope.formlib import form

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import Message as _
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.formlib.schema import EmailLine
from Products.CMFDefault.formlib.form import EditFormBase


def portal_skins(context):
    stool = getToolByName(context, 'portal_skins')
    return SimpleVocabulary.fromValues(stool.getSkinSelections())
    

class IPreferencesSchema(Interface):
    
    email = EmailLine(
                title=_(u"E-mail address")
                )

    listed = Bool(
                title=_(u"Listed status"),
                description=_(u"Select to be listed on the public membership roster.")
                )
    
    portal_skin = Choice(
                title=_(u"Skin"),
                vocabulary="cmf.portal_skins",
                required=False)


class Preferences(EditFormBase):

    form_fields = form.FormFields(IPreferencesSchema)
    base_template = EditFormBase.template
    template = ViewPageTemplateFile("preferences.pt")
    actions = form.Actions(
                form.Action(
                name="change",
                label=u"Change",
                success="handle_success",
                failure="handle_failure"
                    )
                )
                
    def __init__(self, context, request):
        super(Preferences, self).__init__(context, request)
        self.mtool = self._getTool('portal_membership')
        self.stool = self._getTool('portal_skins')
        self.atool = self._getTool('portal_actions')
        
    def get_skin_cookie(self):
        """Check for user cookie"""
        cookies = self.request.cookies
        return cookies.get('portal_skin')

    @property
    def member(self):
        """Get the current user"""
        return self.mtool.getAuthenticatedMember()
        
    def change_password(self):
        """URL for the password form"""
        return self.atool.getActionInfo("user/change_password")['url']
        
    def setUpWidgets(self, ignore_request=False):
        """Populate form with member preferences"""
        data = {}
        data['email'] = self.member.email
        data['listed'] = getattr(self.member, 'listed', None)
        data['portal_skin'] = self.get_skin_cookie()
        
        self.widgets = form.setUpDataWidgets(self.form_fields,
                                        self.prefix,
                                        self.context,
                                        self.request,
                                        data=data,
                                        ignore_request=False)
        
    def handle_success(self, action, data):
        if 'portal_skin' in data:
            self.stool.portal_skins.updateSkinCookie()
        self.member.setProperties(data)
        self.label = _(u"Member changed.")