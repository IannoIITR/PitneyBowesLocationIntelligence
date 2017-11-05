#server for seller
from bottle import route, run, template,response, get, post,request, static_file
import base64
import math
import os
import json
from json import dumps, load

'''
Pitney Bowes App
Unique ID for each phone(IMEI for GSM or MEID for CDMA)
Unique Bar Code or QR code for each package
Each QR code will have a unique phone ID linked to it
each phone id will have latest n GPS coordinates linked to it
'''


BASE_DIRECTORY_STORAGE = "./Data/"
GPS_COORDINATES_LIMIT = 10
DEFAULT_COORDINATES = [[0.0,0.0]]
HOST_IP = '192.168.0.144'

def check_phone_registration(imei_meid):
    print "Checking if registration status of phone: "+imei_meid
    filename = BASE_DIRECTORY_STORAGE+"registeredphones.json"
    with open(filename,"r") as f:
        data = f.read()
        data = json.load(data)
        if(data[imei_meid] == 1):
            print "Phone: "+imei_meid+" registered already"
            return True
        else:
            print "Phone: "+imei_meid+" not registered"
            return False

def register_phone_util(imei_meid):
    print "Received registration request for phone: "+imei_meid
    filename = BASE_DIRECTORY_STORAGE+"registeredphones.json"
    with open(filename,"w+") as f:
        phone_data = f.read()
        if(phone_data == ''):
            phone_data = {}
        else:
            phone_data = json.load(phone_data)
        phone_data[imei_meid] = 1
        json.dump(phone_data,f)

def register_parcel_util(parcel_code, imei_meid):
    print "Registering parcel: "+parcel_code+" with phone: "+imei_meid
    filename = BASE_DIRECTORY_STORAGE+"registeredparcels.json"
    with open(filename,"w+") as f:
        parcel_data = f.read()
        if(parcel_data == ''):
            parcel_data = {}
        else:
            parcel_data = json.load(parcel_data)
        parcel_data[parcel_code] = imei_meid
        json.dump(parcel_data,f)

def check_and_register_phone(imei_meid):
    if(not check_phone_registration(imei_meid)):
        register_phone_util(imei_meid)

def save_phone_location_util(imei_meid, latitude, longitude):
    print "Saving coordinates "+latitude+","+longitude+" for phone "+imei_meid
    check_and_register_phone(imei_meid)
    filename = BASE_DIRECTORY_STORAGE+"phonecoordinates.json"
    with open(filename,"w+") as f:
        data = f.read()
        if(data == ''):
            data = {}
        else:
            data = json.load(data)
        phone_location_data = data.get(imei_meid,[])
        phone_location_data.append([latitude,longitude])
        if(len(phone_location_data) > GPS_COORDINATES_LIMIT):
            phone_location_data = phone_location_data[-GPS_COORDINATES_LIMIT:]
        data[imei_meid] = phone_location_data
        json.dumps(data,f)
        print "Phone: "+imei_meid+" data dumped successfully"

def get_parcel_phone(parcel_code):
    print "Retreiving phone linked with parcel: "+parcel_code
    filename = BASE_DIRECTORY_STORAGE+"registeredparcels.json"
    if(not os.path.exists(filename)):
        return None
    with open(filename,"r") as f:
        data = f.read()
        if(data == ''):
            return None
        else:
            data = json.load(data)
            phone = data.get(parcel_code,None)
            return phone

def get_phone_location(imei_meid):
    if(check_phone_registration(imei_meid)):
        filename = BASE_DIRECTORY_STORAGE+"phonecoordinates.json"
        if(not os.path.exists(filename)):
            return None
        with open(filename,"r") as f:
            data = f.read()
            if(data == ''):
                return DEFAULT_COORDINATES
            else:
                data = json.load(data)
                return data.get(imei_meid,DEFAULT_COORDINATES)
    return DEFAULT_COORDINATES

# pathcode == 1
def register_phone():
    imei_meid = request.forms.get("PhoneID")
    register_phone_util(imei_meid)
    return "Yes"

# pathcode == 2
def register_parcel(request):
    parcel_code = request.forms.get("ParcelCode")
    imei_meid = request.forms.get("PhoneID")
    register_parcel_util(parcel_code, imei_meid)
    return "Yes"

# pathcode == 3
def save_phone_location():
    imei_meid = request.forms.get("PhoneID")
    latitude = request.forms.get("Latitude")
    longitude = request.forms.get("Longitude")
    save_phone_location_util(imei_meid, latitude, longitude)
    return "Yes"

# pathcode == 4
def get_parcel_location():
    parcel_code = request.forms.get("ParcelCode")
    imei_meid = get_parcel_phone(parcel_code)
    response.content_type = 'application/json'
    if(imei_meid is None):
        print "The parcel: "+parcel_code+" has no phone linked with it"
        return "0.0:0.0"
    else:
        route = get_phone_location(imei_meid)
        retval = ""
        for r in route:
            retval += str(r[0])+":"+str(r[1])+","
        return retval[-1]

@post('/get_or_post_info/<pathcode>')
def get_or_post_info(pathcode):
    if(pathcode == '1'):
        return register_phone(request)
    elif(pathcode == '2'):
        return register_parcel(request)
    elif(pathcode == '3'):
        return save_phone_location(request)
    elif(pathcode == '4'):
        return get_parcel_location(request)
    else:
        return "Invalid Request"



# 192.168.208.182
run(host=HOST_IP, port=8080, debug=True)
