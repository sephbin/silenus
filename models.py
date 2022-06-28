from django.contrib.postgres.fields import JSONField
from django.db import models
import django.utils.html as dhtml
import json
import uuid
from django import forms
from django.shortcuts import get_object_or_404
from django.db.models.signals import post_save, m2m_changed, pre_init, post_init, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from background_task import background
from datetime import date
package = str(__package__)

@background()
def background_saveRelative(obtype=None, obid=None, saves=[]):
	#print("background_saveRelative")
	try:
		import sys
		m = get_object_or_404(getattr(sys.modules[__name__], obtype), id=obid)
		for i in saves:
			f = getattr(m,i)
			#print(f)
			try:
				try:
					f.save()
				except Exception as e:
					#print("save Error",e)
					for fl in f.all():
						#print(fl)
						fl.save()
			except: pass
	except: pass

# Custom Fields.
class DataFieldFormField(forms.CharField):

	def prepare_value(self, value):
		try:
			import json
			if value =="{}":
				return value
			else:
				return json.dumps(value)
		except Exception as e:
			return value


class DataField(models.TextField):
	def __init__(self, *args, **kwargs):
		kwargs['max_length'] = 9999
		kwargs['default'] = {}
		kwargs['blank'] = True
		kwargs['null'] = True
		super().__init__(*args, **kwargs)

	def parseString(self, s):
		import json
		try:
			# return "!-%s-!"%(s)
			ns = json.loads(s)
			return ns
		except Exception as e:
			return {}

	def from_db_value(self, value, expression, connection):
		if value is None:
			return {}
		return self.parseString(value)

	def to_python(self, value):
		try:
			py_val = self.parseString(value)
			return py_val
		except Exception as e:
			return {}
	def get_db_prep_save(self, value, connection):
		import json
		try:
			new_value = json.dumps(value)
			return json.dumps(value)
		except Exception as e:
			return json.dumps({"error":str(e)})
	def formfield(self, **kwargs):
		# This is a fairly standard way to set up some defaults
		# while letting the caller override them.
		defaults = {'form_class': DataFieldFormField}
		defaults.update(kwargs)
		return super().formfield(**defaults)


class parentQuerySet(models.query.QuerySet):
	def delete(self, *args, **kwargs):
		#print("queryset delete", self)
		for obj in self:
			if obj.enableDelete:
				obj.delete()
			else:
				obj.enabled = False
				obj.save()
		# super(parentQuerySet, self).filter(enableDelete=True).delete(*args, **kwargs)
		# super(parentQuerySet, self).filter(enableDelete=False).update(enabled=True)

class parentManager(models.Manager):
	def get_queryset(self):
		return parentQuerySet(self.model, using=self._db)

class parentModel(models.Model):
	objects = parentManager()
	previous_state = None
	name =				models.CharField(max_length=256, default = "-empty name-")
	identifier =		models.CharField(max_length=200, default="----", blank=True, null=True)
	enabled =			models.BooleanField(default=True)
	created =			models.DateTimeField(auto_now_add=True)
	updated =			models.DateTimeField(auto_now=True)
	hasError =			models.BooleanField(default=False)
	errorText =			models.TextField(max_length=9999, default="", blank=True, null=True)
	enableDelete =		models.BooleanField(default=False)
	createdBy =			models.CharField(max_length=256, default = "default")
	createdFunction =	models.CharField(max_length=256, default = "admin")
	uniqueCss =			models.TextField(max_length=9999, default="", blank=True, null=True)
	isProcessed = 		models.BooleanField(default=False)

	data =				DataField()
	geometry =			DataField()
	runFunctions =		DataField(help_text='{"functions": [{"function":"clearDataKeys","variables":{}}]}')
	uniqueData =		DataField()
	cssOrder =			[]
	dataOrder =			[]
	relativeSave =		[]
	errorArray =		[]
	dataToFieldMap =	[]
	tempData =			{}

	class Meta:
		abstract = True
	def __str__(self):
		return str(self.id)+": "+self.name
	# # def data(self):
	# 	try:
	# 		return json.loads(self._data)
	# 	except Exception as e:
	# 		return {"error":str(e)}
	def error(self, message = "", he=True):
		if he:
			self.hasError = True
		self.errorArray.append("%s"%(message))
	def delete_start(self):
		pass

	def delete_end(self):
		pass
	def process(self, saveModel=True):
		self.isProcessed = True
		if saveModel:
			self.save()
		pass
	def delete(self):
		self.delete_start()
		#print("delete: %s" %(self))
		if self.enableDelete:
			super(parentModel, self).delete()
		else:
			self.enabled = False
			try:	self.quantity = 0
			except:	pass
			self.save()
		self.delete_end()

	def save_start(self):
		##print("default: save_start")
		pass

	def save_end(self):
		##print("default: save_end")
		pass

	def save(self, *args, **kw ):
		self.errorArray = []
		self.hasError = False
		##print("default: save")
		self.save_start()
		# self.runAllFunctions()
		# self.data = self.set_data
		try:
			upd = self.previous_state["data"]
			##print(upd)
			if upd != self.uniqueData:
				upd.update(self.uniqueData)
				self.uniqueData = upd
		except Exception as e: pass
		# self.runFunctions = {"functions":[
		# 	{"function":"placeholder","variables":{}},
		# 	# {"function":"delDataKeys","variables":["error","class","containerInherit"]}
		# 	]}
		# self.dataToFields()
		self.errorText = "\n".join(self.errorArray)
		super( parentModel, self ).save( *args, **kw )
		# self.saveRelative()
		self.save_end()


	@staticmethod

	# @receiver(post_init, self)
	def remember_state(sender, **kwargs):
		##print("remember_state internal")
		##print(sender)
		try:
			instance = kwargs.get('instance')
			remember = {
				"data": instance.uniqueData,
				"geometry": instance.geometry,
			}
			instance.previous_state = remember
		except: pass

class dataSet(parentModel):
	pass

class dataItem(parentModel):
	dataSet =		models.ForeignKey(dataSet, on_delete= models.SET_NULL, blank=True, null=True)
	dataPacket =	models.ForeignKey('dataPacket', on_delete=models.SET_NULL, blank=True, null=True, related_name="dataItems")
	processed =		models.BooleanField(default=False)
	charField01 =	models.CharField(max_length=256, blank=True, null=True)
	charField02 =	models.CharField(max_length=256, blank=True, null=True)
	charField03 =	models.CharField(max_length=256, blank=True, null=True)
	charField04 =	models.CharField(max_length=256, blank=True, null=True)
	charField05 =	models.CharField(max_length=256, blank=True, null=True)
	charField06 =	models.CharField(max_length=256, blank=True, null=True)
	charField07 =	models.CharField(max_length=256, blank=True, null=True)
	charField08 =	models.CharField(max_length=256, blank=True, null=True)
	charField09 =	models.CharField(max_length=256, blank=True, null=True)
	numField01 =	models.FloatField(blank=True, null=True)
	numField02 =	models.FloatField(blank=True, null=True)
	numField03 =	models.FloatField(blank=True, null=True)
	numField04 =	models.FloatField(blank=True, null=True)
	numField05 =	models.FloatField(blank=True, null=True)
	numField06 =	models.FloatField(blank=True, null=True)
	numField07 =	models.FloatField(blank=True, null=True)
	numField08 =	models.FloatField(blank=True, null=True)
	numField09 =	models.FloatField(blank=True, null=True)
	fieldMap =		DataField()

	@property
	def getDictionary(self):
		outDict = {"pk":self.pk, "processed":self.processed}
		for k, v in self.dataSet.data.items():
			value = getattr(self, v["field"])
			outDict[k] = value
		return outDict

class dataPacket(parentModel):
	assigned_computer	=	models.CharField(max_length=256, blank=True, null=True)
	dataSet =				models.ForeignKey('dataSet', on_delete=models.SET_NULL, blank=True, null=True)			
	completed =				models.BooleanField(default=False)

	@property
	def dataItemList(self):
		return self.dataItems.all()
	@property
	def dataItemList_uprocessed(self):
		return self.dataItems.filter(processed=False)



@receiver(post_save, sender=dataPacket)
def add_to_dataPacket(sender, instance, created, **kwargs):
	print("Saved dataPacket", instance.completed)
	if created:
		try:
			dataItem_first = dataItem.objects.filter(dataPacket=None).first()
			print(dataItem_first)
			dataItem_instances = dataItem.objects.filter(dataPacket=None, dataSet=dataItem_first.dataSet)[:100]
			for dataItem_instance in dataItem_instances:
				dataItem_instance.dataPacket = instance
				dataItem_instance.save()
		except:	pass
		if len(dataItem_instances) == 0:
			instance.completed = True
			instance.save()

@receiver(post_save, sender=dataItem)
def check_data_packet_complete(sender, instance, created, **kwargs):
	if instance.dataPacket:
		dataPacket_instance = instance.dataPacket
		count = dataPacket_instance.dataItemList_uprocessed.count()
		print("count",count)
		if count == 0:
			dataPacket_instance.completed = True
			dataPacket_instance.save()

# 	data = {"data":instance.data}
# 	#print(">>>","create connections")
# 	conA, created = connection.objects.update_or_create(
# 		name				=	str(instance.container_stranger)+" -> "+str(instance.container_parent),
# 		connector_parent	=	instance,
# 		container_from		=	instance.container_stranger,
# 		container_to		=	instance.container_parent,
# 		project				=	instance.project,
# 		elementCategory			=	get_object_or_404(elementCategory, name="door direction"),
# 		defaults			=	data
# 		)

# 	conB, created = connection.objects.update_or_create(
# 		name				=	str(instance.container_parent)+" -> "+str(instance.container_stranger),
# 		connector_parent	=	instance,
# 		container_from		=	instance.container_parent,
# 		container_to		=	instance.container_stranger,
# 		project				=	instance.project,
# 		elementCategory			=	get_object_or_404(elementCategory, name="door direction"),
# 		defaults			=	data
# 		)

