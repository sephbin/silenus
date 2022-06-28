from django.contrib  import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test

import sys, os
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from .models import *
# import ghhops_server as hs
import rhino3dm

def getPayload(request):
	import json
	d = {}
	try:
		d = json.loads(str(request.body, encoding='utf-8'))
	except Exception as e:
		print(e)
		if request.method == "GET":
			try:	d = dict(request.GET)
			except: pass
		if request.method == "POST":
			try:	d = dict(request.POST)
			except: d = json.loads(str(request.body, encoding='utf-8'))
		if request.method == "DELETE":
			try:	d = json.loads(str(request.body, encoding='utf-8'))
			except: pass
	return d

def errorLog(e, log=[]):
	exc_type, exc_obj, exc_tb = sys.exc_info()
	other = sys.exc_info()[0].__name__
	fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
	errorType = str(exc_type)
	errob = {"isError": True, "error":str(e), "errorType":errorType, "function":fname, "line":exc_tb.tb_lineno, "log":log}
	return errob

def getSecure():
	try:
		file = open("C:\\secure\\secure.json",
			"r")
		out = file.read()
		file.close()
		return json.loads(out)
	except Exception as e:
		#dblog(e)
		return {}

def isUser(request):
	user = None
	try:	sqlcheck(request, getSecure()["dtvsn"]["username"], getSecure()["dtvsn"]["password"])
	except: pass
	try:
		bearer = request.META["HTTP_AUTHORIZATION"].replace("Bearer ","")
		dblog(bearer)
		try:
			dblog("try")
			srequ = get_object_or_404(samlrequest, nonce = bearer)
			dblog("Try worked")
			dblog(srequ)
		except Exception as e:
			dblog("except")
			dblog(e)
			srequ = get_object_or_404(standardrequest, nonce = bearer)
			dblog("Except worked")
			dblog(srequ)
		user = srequ.user
	except:
		if request.user.is_authenticated:
			user = request.user
	return user
def from_json(json_obj):
	"""Convert to rhino3dm from json"""
	return rhino3dm.CommonObject.Decode(json_obj)

def _coerce_value(param_type, param_data):
	import rhino3dm
	import json
	# get data as dict
	
	# parse data
	print(param_type)
	if param_type.startswith("Rhino.Geometry.Point3d"):
		data = json.loads(param_data)
		data = {k.lower(): v for k, v in data.items()}
		return rhino3dm.Point3d(**data)
	if param_type.startswith("Rhino.Geometry."):
		data = json.loads(param_data)
		return from_json(data)
	if param_type.startswith("System.String"):
		data = eval(param_data)
		try: data = json.loads(data)
		except Exception as e: print(e)
		return data
	return param_data

def parse_params(payload):
	outOb = {"payload":payload, "data":{}}
	for hopsInput in payload["values"]:
		# print(hopsInput)
		upOb = []
		for treeAdress, treeBranch in hopsInput["InnerTree"].items():
			apOb = []
			for hopsObject in treeBranch:
				try:
					a = _coerce_value(hopsObject["type"],hopsObject["data"])
					apOb.append(a)
					# print("-"*4,a)
				except Exception as e:
					apOb.append(None)
					print(errorLog(e))
					pass
			upOb.append(apOb)
		if len(upOb) < 2:
			upOb = upOb[0]
		outOb[hopsInput["ParamName"]] = upOb
	# for inputStream in outOb["payload"]["values"]:
	# 	outOb["data"][inputStream["ParamName"]] = inputStream["InnerTree"]["0"]
	return outOb


@csrf_exempt
def processcsv(request):
	structure = {
			"Python": {"version":str(sys.version), "info":str(sys.version_info)},
			"Description": "Parses CSV into data tree",
			"Inputs": [
				{"Name": "CSV", "Nickname": "CSV", "Description": "CSV", "ParamType": "Text", "ResultType": "System.String", "Default":None, "AtLeast": 1, "AtMost": 2147483647},
				{"Name": "Settings", "Nickname": "S", "Description": "Settings", "ParamType": "Text", "ResultType": "System.String", "Default":None, "AtLeast": 1, "AtMost": 1},
			],
			"Outputs": [{"Name": "Log", "Nickname": "L", "Description": "Log", "ParamType": "Text", "ResultType": "System.String", "AtLeast": 1, "AtMost": 1},
				{"Name": "Output", "Nickname": "O", "Description": "Output", "ParamType": "Text", "ResultType": "System.String", "AtLeast": 1, "AtMost": 1},
			]}
	if request.method =="GET":
		return JsonResponse(structure)

	elif request.method =="POST":
		import csv
		from io import StringIO
		log = []
		payload = parse_params(getPayload(request))
		print(">>",payload)
		outOb = None
		for csvString in payload["CSV"]:
			f = StringIO(csvString)
			reader = list(csv.reader(f, delimiter=','))
			reader = list(map(lambda x: {"type": "System.String", "data": "\""+"\t".join(x)+"\""}, reader))
			outOb = reader
		out = {"values": [
			{"ParamName": "Log", "InnerTree": {"0": [{"type": "System.String", "data": ""}], }},
			{"ParamName": "Output", "InnerTree": {"0": outOb, }},
		]}
		print(out)
		return JsonResponse(out)

	else:
		print("?")
		return JsonResponse({"error":True})


@csrf_exempt
def meshOclusion(request):
	structure = {
			"Python": {"version":str(sys.version), "info":str(sys.version_info)},
			"Description": "Parses CSV into data tree",
			"Inputs": [
				{"Name": "Settings", "Nickname": "S", "Description": "Settings", "ParamType": "Text", "ResultType": "System.String", "Default":None, "AtLeast": 1, "AtMost": 1},
			],
			"Outputs": [
				{"Name": "Log", "Nickname": "L", "Description": "Log", "ParamType": "Text", "ResultType": "System.String", "AtLeast": 1, "AtMost": 1},
				{"Name": "Output", "Nickname": "O", "Description": "Output", "ParamType": "Text", "ResultType": "System.String", "AtLeast": 1, "AtMost": 1},
			]}
	if request.method =="GET":
		return JsonResponse(structure)

	elif request.method =="POST":
		log = []
		payload = parse_params(getPayload(request))
		# print(payload)
		outOb = [{"type": "System.String", "data": "\"OUT\""}]

		out = {"values": [
			{"ParamName": "Log", "InnerTree": {"0": [str(log)], }},
			{"ParamName": "Output", "InnerTree": {"0": outOb, }},
		]}
		# print(out)
		return JsonResponse(out)

	else:
		print("?")
		return JsonResponse({"error":True})

@csrf_exempt
def createData(request):
	structure = {
			"Python": {"version":str(sys.version), "info":str(sys.version_info)},
			"Description": "Saves",
			"Inputs": [
				{"Name": "Data_Set", "Nickname": "DS", "Description": "Data Set", "ParamType": "Text", "ResultType": "System.String", "Default":None, "AtLeast": 1, "AtMost": 1},
				{"Name": "Data_Keys", "Nickname": "K", "Description": "Data Keys", "ParamType": "Text", "ResultType": "System.String", "Default":None, "AtLeast": 1, "AtMost": 2147483647},
				{"Name": "Data_Values", "Nickname": "V", "Description": "Data Values", "ParamType": "Text", "ResultType": "System.String", "Default":None, "AtLeast": 1, "AtMost": 2147483647},
			],
			"Outputs": [
				{"Name": "Log", "Nickname": "L", "Description": "Log", "ParamType": "Text", "ResultType": "System.String", "AtLeast": 1, "AtMost": 1},
				{"Name": "Output", "Nickname": "O", "Description": "Output", "ParamType": "Text", "ResultType": "System.String", "AtLeast": 1, "AtMost": 1},
			]}

	if request.method =="GET":
		return JsonResponse(structure)
	elif request.method =="POST":
		log = []
		payload = parse_params(getPayload(request))
		print(payload)
		for data_set in payload["Data_Set"]:
			data_set_ob, created = dataSet.objects.update_or_create(name=data_set)
			print(data_set_ob.data)
			search_kwargs = {}
			defaults_kwargs = {}
			for k, v in zip(payload["Data_Keys"],payload["Data_Values"]):
				print(data_set, k, v)
				if k.startswith("_"):
					ko = data_set_ob.data[k.replace("_","")]["field"]
					search_kwargs[ko] = v
				else:
					ko = data_set_ob.data[k]["field"]
					defaults_kwargs[ko] = v
			print(search_kwargs)
			print(defaults_kwargs)
			search_kwargs["dataSet"]=data_set_ob
			search_kwargs["defaults"]=defaults_kwargs
			dataItem_instance, created = dataItem.objects.update_or_create(**search_kwargs)
			print(dataItem_instance, created)

		outOb = [{"type": "System.String", "data": "\"OUT\""}]

		out = {"values": [
			{"ParamName": "Log", "InnerTree": {"0": [{"type": "System.String", "data": str(log)}], }},
			{"ParamName": "Output", "InnerTree": {"0": outOb, }},
		]}
		# print(out)
		return JsonResponse(out)

	else:
		print("?")
		return JsonResponse({"error":True})
	instance_model = getattr(sys.modules[__name__], change["model"])
	instance, created = instance_model.objects.update_or_create(**change["kwargs"])


def checkForWork(request):
	log = []
	computer_id = request.GET.get('computer-id')
	dataPacket_instances = dataPacket.objects.filter(assigned_computer=computer_id, enabled=True, completed=False)
	if dataPacket_instances.count() == 0:
		new_dataPacket = dataPacket(assigned_computer=computer_id)
		new_dataPacket.save()

		log.append("new dataPacket")
	else:
		new_dataPacket = dataPacket_instances.first()
		log.append("existing dataPacket")
	packetData = []
	# print(new_dataPacket.pk, new_dataPacket)
	for dataItemInstance in new_dataPacket.dataItems.filter(processed=False).order_by('pk'):
		packetData.append(dataItemInstance.getDictionary)
	return JsonResponse({"isSuccess": True, "log":log, "packetData":packetData})