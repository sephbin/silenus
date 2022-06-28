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
from datetime import date
from .models_utils import *


class graphObject(parentModel):
	pass

class geometryObject(parentModel):
	pass

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

