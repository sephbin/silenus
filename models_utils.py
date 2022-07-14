from django.db import models
import json
from django import forms
package = str(__package__)

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
		kwargs['max_length'] = 999999
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

	@property
	def css( self):
		out_css = ""
		for step in self.cssOrder:
			try:	out_css += getattr(self,step).uniqueCss+"\n"
			except:	pass
		out_css += self.uniqueCss
		return out_css
	class Meta:
		abstract = True
	def __str__(self):
		return str(self.id)+": "+self.name
	# # def data(self):
	# 	try:
	# 		return json.loads(self._data)
	# 	except Exception as e:
	# 		return {"error":str(e)}
	# def saveRelative(self):
	# 	#print("saveRelative")
	# 	#print(self.relativeSave)
	# 	for i in self.relativeSave:
	# 		try:
	# 			background_saveRelative(self.__class__.__name__, self.id, self.relativeSave)
	# 		except Exception as e:
	# 			#print(e)
	# 			pass
	def error(self, message = "", he=True):
		if he:
			self.hasError = True
		self.errorArray.append("%s"%(message))
	def delDataKeys(self, keys=[]):
		##print("delDataKeys")
		for k in keys:
			try:
				del self.previous_state["data"][k]
				##print(self.previous_state["data"])
			except:	pass
		self.uniqueData = self.previous_state["data"]
	def clearDataKeys(self, variables):
		#print("CLEARDATAKEYS")
		self.previous_state["data"] = {}
	@property
	def clearCss(self):
		pass
	def getKey(self,key):
		if key in self.data:
			return self.data[key]
		else:
			return None
	@property
	def modelClass(self):
		return self.getKey("class")
	
	def runAllFunctions(self, application=None):
		#print("runAllFunctions")
		try:
			#print(self.runFunctions)
			for f in self.runFunctions["functions"]:
				try:
					#print(f)
					getattr(self,f["function"])(f["variables"])
				except: pass
		except Exception as e:	return {"error": str(e)}
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
		self.errorText = "\n".join(self.errorArray)
		super( parentModel, self ).save( *args, **kw )
		# self.saveRelative()
		self.save_end()


	@staticmethod
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