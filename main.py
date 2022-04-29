
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
from uuid import uuid4
import json
#import requests


 # Only start connections when the request is valid. 200 and 400 responses.


 # Only start connections when the request is valid. 200 and 400 responses.

def addServerConnection(host, user, password, db):
    connection = None
    try:
        connection = mysql.connector.connect(
            host= host,
            user= user,
            password= password,
            database= db
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")

    return connection

connection = addServerConnection("localhost", "root", "1234", "seniorProject") #create connection to database named seniorProject

def addDatabase(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        if query != "":
            print("Database created successfully")
    except Error as err:
        print(f"Error: '{err}'")

def executeQuery(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query successful")
    except Error as err:
        print(f"Error: '{err}'")

def toDict(item): #convert results from MySql query from string to dict
    data = json.loads(item)
    return data
def toString(item):
    return json.dumps(item)
# CREATE Functions
def createEventID():
    eventID = str(datetime.now().strftime('%Y-%m-%d-%H:%M:%S-')+str(uuid4())) # generate unique id with timestamp and unique uuid4 sequence
    return eventID

def createEstimateDueDate(event):
    for i in event["intervals"]: #find components maximum number of days available
        if i["unit"].lower() == "days": #if interval is in days get next due date
            date = datetime.strptime(i["lastEventDate"], "%m-%d-%Y")  + timedelta(days = int(i["value"]))
            return date.strftime("%m-%d-%Y")

def priorityLevel(event): #priority levels lowest 1-6 highest
    date = datetime.today()
    lastDate = datetime.strptime(event["lastEventDate"], "%m-%d-%Y")
    zoneSize = 0
    day = (date - lastDate).days
    for i in event["intervals"]:
        if i["unit"].lower() == "days": #if interval is in days get priority levels
            zoneSize = int(i["value"]) / 6
            return day // zoneSize
                
# GET Functions
def getQuery(connection, query): #function to retrieve data from database 
    cursor = connection.cursor(dictionary=True) #set cursor to retrieve data in dict type
    try:
        cursor.execute(query)
        return cursor.fetchone() #fetchall()
    except Error as err:
        print(f"Error: '{err}'")

def getEvent(eventID = None): #get event with provided eventID
    if eventID == None: #return all events
        query = query = f"SELECT event FROM events"
        event = getQuery(query)
    else:
        query = f"SELECT event FROM events WHERE eventID = '{eventID}';"
        event = getQuery(query)
    if(event!=None):
        #print(event)
        data = toDict((event["event"]))
        return data
    else: 
        print("getQuery returned None")
        return None

def getPartLogs(serial = None, name = None, position = None):
    if serial == None and name == None and position == None: #return all part logs
        query = "SELECT ALL partLog FROM partLogs"
    elif serial != None and name == None and position == None:
        query = f"SELECT partLog FROM partLogs WHERE serial LIKE {serial};"
    elif serial == None and name != None and position == None:
        query = f"SELECT partLog FROM partLogs WHERE name LIKE {name};"
    elif serial == None and name == None and position != None:
        query = f"SELECT partLog FROM partLogs WHERE position LIKE {position};"
    elif serial != None and name != None and position == None:
        query = f"SELECT partLog FROM partLogs WHERE serial LIKE {serial} AND name LIKE {name};"
    elif serial != None and name == None and position != None:
        query = f"SELECT partLog FROM partLogs WHERE serial LIKE {serial} AND position LIKE {position};"
    elif serial == None and name != None and position != None:
        query = f"SELECT partLog FROM partLogs WHERE name LIKE {name} AND position LIKE {position};"
    log = getQuery(query)
    return toDict(log['partLog'])

def getPart(serial = None, cagID = None): #getParts with asssociated serial and/or cagID
    if cagID == None and serial == None: # return all parts
        query = f"SELECT ALL part FROM parts;"
    elif serial == None: #return all parts associated with provided cagID
        query = f"SELECT part FROM parts WHERE cagID = '{cagID}';"
    elif cagID == None: #return all parts associated with provided serial num
        query = f"SELECT part FROM parts WHERE serial = '{serial}';"
    elif serial != None and cagID != None: #return parts with provided serial cagID
        query = f"SELECT part FROM parts WHERE serial = '{serial}' AND cagID = '{cagID}';"
    part= getQuery(connection, query)
    return toDict(part["part"])

def getAircraft(cagID): #get aircraft with provided cagID
    query = f"SELECT aircraft FROM aircraft WHERE cagID = '{cagID}'"
    aircraft = getQuery(connection, query)
    return toDict(aircraft['aircraft'])

# POST Functions
def postAircraft(aircraft):
    values = "\'{}\', \'{}\'".format(str(aircraft["cagID"]), toString(aircraft))
    query = "INSERT INTO aircraft VALUES (" + values + ");"
    executeQuery(connection, query) # separate database from logic

def postEvents(event):
    event["eventID"] = str(createEventID())
    event["estimatedDueDate"] = createEstimateDueDate(event)

    values = "\'{}\', \'{}\', \'{}\'".format(str(event["eventID"]), str(event["serial"]),toString(event))
    query = "INSERT INTO events VALUES (" + values + ");"

   # print(query)
    executeQuery(connection, query) # separate database from logic

def postParts(part):
    print(part)
    values = "\'{}\', \'{}\', \'{}\'".format(str(part["serial"]), str(part["cagID"]),toString(part))
    query = "INSERT INTO parts VALUES (" + values + ");"

    print(query)
    executeQuery(connection, query) # separate database from logic

def postPartLogs(partLog):
    values = "\'{}\', \'{}\', \'{}\', \'{}\'".format(str(partLog["serial"]), str(partLog["name"]), str(partLog["position"]), toString(partLog))
    query = "INSERT INTO partLogs VALUES (" + values + ");"

    print(query)
    executeQuery(connection, query) # separate database from logic

# PUT Functions
def putAircraft(aircraft:dict):
    query = "SET SQL_SAFE_UPDATES=0;"
    executeQuery(connection, query)
    cagID = aircraft["cagID"]
    query = 'UPDATE aircraft set aircraft = "' + str(aircraft) + '" WHERE cagID = ' + str(aircraft["cagID"]) + ';'
    executeQuery(connection, query)
    query = "SET SQL_SAFE_UPDATES=0;"
    executeQuery(connection, query)

def putPartNewEvent(event):    ##########################if part[events] = empty handling?
    #get maintenance event type
    type = event["maintenanceType"]
    #get list of events related to current event part
    part = getPart(serial = event["serial"])
    #find event in list that is of same matenanceType
    typeList = []
    for i in part["events"]: #######################thinks it's in there when it's not
        eID = getEvent(str(i))
        if(eID==None): break 
        typeList.append(eID["maintenanceType"])
    # print(eID, event)
        if eID["maintenanceType"] == type:  #replace eventID in parts active events list if found
            part["events"] = [event["eventID"] if item == eID["eventID"] else item for item in part["events"]]
       #check to see if there is already an eventID for that maintenance type and if not add it to the end of the list     
    if type not in typeList:
        part["events"].append(event["eventID"])
    query = "SET SQL_SAFE_UPDATES=0"
    executeQuery(connection, query)
    values = "'{" + "\"serial\" : \"{}\", \"cagID\" : \"{}\", \"name\" : \"{}\", \"position\" : \"{}\", \"events\" : ".format(
        str(part["serial"]), str(part["cagID"]), str(part["name"]), str(part["position"])) + str(part["events"]).replace("'", '\"') + "}'"
    query = "UPDATE parts SET part = " + values + " WHERE serial like '" + event["serial"] + "'"
    executeQuery(connection,query)
    #replace that item in the list and update database

# DELETE Functions
def deleteEvent(eventID):
    query = "UPDATE events SET event = REPLACE(event, 'in_progress', 'completed') WHERE eventID = '" + eventID + "';"
    executeQuery(connection, query)

def deletePart(serial):
   query = "SET foreign_key_checks=0"
   executeQuery(connection, query)
   query = "DELETE FROM parts WHERE serial = '" + serial + "';"
   executeQuery(connection, query)
   query = "SET foreign_key_checks=1"
   executeQuery(connection, query)

def deleteAircraft(cagID):
    query = "SET foreign_key_checks=0"
    executeQuery(connection, query)
    query = "DELETE FROM aircraft WHERE cagID = '" + cagID + "';"
    executeQuery(connection, query)
    query = "SET foreign_key_checks=1"
    executeQuery(connection, query)

def deletePartLog(serial, startDate, endDate):
    query = "DELETE FROM partLogs WHERE serial = '" + serial + "' AND partLog LIKE '%" + startDate + "%' AND partLog LIKE '%" + endDate + "%';"
    executeQuery(connection, query)



def requests(request):
    if request["commonParms"]["action"].lower() == "get":
        return getRequestHandler(request["request"])
    elif request["commonParms"]["action"].lower() == "edit":
        putRequestHandler(request)
    elif request["commonParms"]["action"].lower() == "delete":
        deleteRequestHandler(request["request"])
    elif request["commonParms"]["action"].lower() == "write":
        postRequestHandler(request["request"])
        print('post')

def getRequestHandler(struct):
    if struct["type"].lower() == 'part':
        return getPart(serial = struct["identifiers"]["serial"], cagID = struct["identifiers"]["cagID"])
    elif struct["type"].lower() == 'event':
        return getEvent(eventID = struct["identifiers"]["eventID"])
    elif struct["type"].lower() == 'log':#getPartLogs(serial = None, name = None, position = None)
        return getPartLogs(serial = struct["identifiers"]["serial"],name = struct["identifiers"]["name"],position = struct["identifiers"]["position"] )
    if struct["type"].lower() == 'aircraft':
        return getAircraft(cagID = struct["identifiers"]["cagID"])


def postRequestHandler(struct):
    if struct["type"].lower() == 'part':
        return postParts(struct["identifiers"])
    elif struct["type"].lower() == 'event':
        return postEvents(struct["identifiers"])
    elif struct["type"].lower() == 'log':#getPartLogs(serial = None, name = None, position = None)
        return postPartLogs(struct["identifiers"])
    if struct["type"].lower() == 'aircraft':
        return postAircraft(struct["identifiers"])


def putRequestHandler(struct):
    if struct["request"]["type"].lower() == 'part':
        deletePart(struct["request"]["identifiers"]["serial"])
        postParts(struct["request"]["identifiers"])
        #######################currently just deletes old entry and makes a new one. There are multiple put request types and they both need to be finished before finishing this
        print("putPartRequest")
        return
    elif struct["request"]["type"].lower() == 'partlog':
        deletePartLog(struct["request"]["identifiers"]["serial"], struct["request"]["identifiers"]["startDate"], struct["request"]["identifiers"]["endDate"])
        postPartLogs(struct["request"]["identifiers"])
        print("putPartLogRequest")
        return
    elif struct["request"]["type"].lower() == 'event': #delete event just sets the old event to complete so it doesnt remove the entry
        deleteEvent(struct["request"]["identifiers"]["eventID"])
        postEvents(struct["request"]["identifiers"])
        print("putEventRequest")
        return
    elif struct["request"]["type"].lower() == 'aircraft':
        putAircraft(struct["request"]["identifiers"])
        print("putAircraftRequest")
    else : print("Failed")

def deleteRequestHandler(struct):
   if struct["type"].lower() == 'part':
       return deletePart(struct["identifiers"]["serial"])
   elif struct["type"].lower() == 'event':
       return deleteEvent(struct["identifiers"]["eventID"])
   elif struct["type"].lower() == 'log':
       return deletePartLog(struct["identifiers"]["serial"], struct["identifiers"]["startDate"],
                            struct["identifiers"]["endDate"])
   elif struct["type"].lower() == 'aircraft':
       return deleteAircraft(struct["identifiers"]["cagID"])



# TESTING PURPOSES BELOW
aircraftTest = {
    "cagID" : "1002",
    "supplierID" : "999",
    "aircraftMake" : "Boeing",
    "aircraftModel" : "777"
}
partTest = {
    "serial": "10a1",
    "name": "engine",
    "position": "1",
    "events" : []
}

partLogTest = {
    "cagID": "1001",
    "serial": "10a1",
    "name": "engine",
    "position": "1",
    "startDate" : "10/10/2000",
    "endDate" : "10/15/2001",
    "events" : []
}

eventTest = {   
    "eventID": "2002-3asdf",
    "cagID" : "1002",
    "serial" : "10a1",
    "name": "engine",
    "position": "1",
    "intervals" : [
        {
            "unit" : "days",
            "value" : "60",
            "bufferValue" : "90",
            "lastEventDate" : "04-07-2022"
        }
    ],
    "maintenanceType" : "transmission",
    "maintenanceSubType" : "engine",
    "esimatedDueDate" : "",
    "dueDate" : "today",
    "unit" : "minutes",
    "eventDescription" : "asdf",
    "documentName" : "Document Name",
    "documentLoc" : "URL",
    "eventStatus" : "in_progress",
    "eventPriority" : 1,
    "lastEventDate" : "03-22-2022"
}

postEvents(eventTest)

##################################################################################
testPartRequest = {
    "commonParms" : {
    "action": "get",
    "view": "maintenance",
    "version": "1.0.0"
    },
    "request": {
        "type" : "part",
        "identifiers":{
            "cagID": "1001",
            "serial": "10aaa1",
            "name": "engine",
            "position": "1",
            "events" : ["asdf"]
        }
    }
}
print(requests(testPartRequest))

