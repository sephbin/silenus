import sys
from django.contrib import admin
from .models import *
from django_admin_search.admin import AdvancedSearchAdmin
from .form import *

m_list_display = ['enabled','enableDelete','pk','identifier','name','hasError','updated',]
m_list_editable = ['enabled', 'enableDelete',]
m_list_display_links = ['name',]
m_list_filter = ['enabled','enableDelete']
m_search_fields = ["name","data","identifier",]
m_readonly_fields = []
m_actions = ['hardDeleteSelected', 'resaveSelected', 'enableDeleteSelected', 'disableDeleteSelected', 'clearIdentifierSelected', ]

m_save_on_top = True
m_save_as = True



# Register your models here.
class master(AdvancedSearchAdmin):
	search_form = masterAdvancedSearch
	list_display = m_list_display
	list_editable = m_list_editable
	list_display_links = m_list_display_links
	search_fields = m_search_fields
	readonly_fields = m_readonly_fields
	list_filter = m_list_filter
	actions = m_actions
	save_on_top = m_save_on_top
	save_as = m_save_as
	list_per_page = 25

	def resaveSelected(self, request, queryset):
		for q in queryset:
			q.save()
	resaveSelected.short_description = "Resave Selected"
	def enableDeleteSelected(self, request, queryset):
		queryset.update(enableDelete=True)
	enableDeleteSelected.short_description = "Enable Delete Selected"
	def disableDeleteSelected(self, request, queryset):
		queryset.update(enableDelete=False)
	disableDeleteSelected.short_description = "Disable Delete Selected"
	def clearIdentifierSelected(self, request, queryset):
		queryset.update(identifier=None)
	clearIdentifierSelected.short_description = "Clear Identifier Selected"

	def hardDeleteSelected(self, request, queryset):
		for q in queryset:
			q.enableDelete = True
			q.delete()
	hardDeleteSelected.short_description = "Hard Delete Selected"

class dataPacket_admin(master):
	
	readonly_fields = m_readonly_fields + ["dataItemList",]

class dataItem_admin(master):
	list_filter = m_list_filter + ["processed"]
	readonly_fields = m_readonly_fields + ["getDictionary",]
	def setProcessedTrue(self, request, queryset):
		queryset.update(processed=True)
	setProcessedTrue.short_description = "setProcessedTrue"
	def setProcessedFalse(self, request, queryset):
		queryset.update(processed=False)
	setProcessedFalse.short_description = "setProcessedFalse"
	actions = ['setProcessedTrue','setProcessedFalse',]

for subclass in parentModel.__subclasses__():
	try:
		try:
			adminName = str(subclass.__name__)+"_admin"
			adminOb = getattr(sys.modules[__name__], adminName)
		except Exception as e:
			adminOb = master
		admin.site.register(subclass, adminOb)
	except: pass