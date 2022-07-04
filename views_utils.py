from .models import *
import sys, os
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
def to_json(rhino_geom):
	return rhino3dm.CommonObject.Encode(rhino_geom)

def to_hops_json(rhino_geom):
	class_name = rhino_geom.__class__.__name__
	outOb = {"type": "Rhino.Geometry.%s"%(class_name), "data":
		json.dumps(to_json(rhino_geom))
		}
	return outOb

def _coerce_value(param_type, param_data):
	import rhino3dm
	import json
	# get data as dict
	
	# parse data
	# print(param_type)
	if param_type.startswith("Rhino.Geometry.Point3d"):
		data = json.loads(param_data)
		data = {k.lower(): v for k, v in data.items()}
		return rhino3dm.Point3d(**data)
	if param_type.startswith("Rhino.Geometry."):
		try:	data = json.loads(param_data)
		except:	data = param_data
		return from_json(data)
	if param_type.startswith("System.String"):
		data = eval(param_data)
		try:
			data = json.loads(data)
			if "archive3dm" in data and "opennurbs" in data:
				data = _coerce_value("Rhino.Geometry.", data)
		except Exception as e: print(e)
		# print("string",data)
		return data
	return param_data

def parse_params(payload):
	try:
		outOb = {"payload":payload}
		for hopsInput in payload["values"]:
			# print(hopsInput)
			upOb = []
			for treeAdress, treeBranch in hopsInput["InnerTree"].items():
				apOb = []
				outOb[hopsInput["ParamName"]+"_original"] = treeBranch
				for hopsObject in treeBranch:
					# print("hopsObject",hopsObject)
					try:
						a = _coerce_value(hopsObject["type"],hopsObject["data"])
						apOb.append(a)
						# print("-"*4,a)
					except Exception as e:
						apOb.append(None)
						# print(errorLog(e))
						pass
				upOb.append(apOb)
			if len(upOb) < 2:
				upOb = upOb[0]
			outOb[hopsInput["ParamName"]] = upOb
	except Exception as e:
		print(errorLog(e))
		pass
	return outOb