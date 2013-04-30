#! /usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser
import argparse

import gflags
import httplib2
import keyring
import sys
import datetime



from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run

def today():
	return todayDate.isoformat()

def tomorrow():
	return (todayDate + datetime.timedelta(days=1)).isoformat()

def nextWeek():
	return (todayDate + datetime.timedelta(days=7)).isoformat()

def nextMonth():
	return (todayDate + datetime.timedelta(days=30)).isoformat()	

def dueDate(due):
	due = due.lower()
	if weekdays.has_key(due) and weekdays[due] > todayDate.isoweekday(): 
		diff = weekdays[due] - todayDate.isoweekday()
		dueDate = (todayDate + datetime.timedelta(diff)).isoformat()
	elif weekdays.has_key(due) and weekdays[due] <= todayDate.isoweekday():
		diff = 6 - todayDate.isoweekday()
		dueDate = (todayDate + datetime.timedelta(diff)).isoformat()
	elif relDays.has_key(due):	    
		dueDate = relDays[due]()
	else: 
		dueDate = due
	return dueDate+'T12:00:00.000Z'

def tasks(listID):
	tasks = service.tasks().list(tasklist=listID).execute()
	n=1
	try: 
		for task in tasks['items']:
			if task['title'] == '': pass
			else:
				taskName=task['title']
				dueDate='No date.'
				if 'due' in task: 
					fullDueDate=str(task['due'])
					dueDate=fullDueDate[:10]
				
				if 'parent' in task.keys():
					task['taskNum'] = n					
					print '       '+str(task['taskNum'])+'. '+task['title'].encode('utf-8', 'ignore')+' : '+dueDate
					n+=1
				else: 
					task['taskNum'] = n
					print '    '+str(n)+'. '+task['title'].encode('utf-8', 'ignore')+' : '+dueDate
					n += 1
	except KeyError: print '    No tasks.'

def listTasks(listName, tasklists):
	if listName == []:
		for tasklist in tasklists['items']:
			print tasklist['title']
			listID=tasklist['id']
			tasks(listID)					
			print
	else:
		for tasklist in tasklists['items']:
			if tasklist['title'] != listName[0]: pass
			else:
				print tasklist['title']
				listID=tasklist['id']
				tasks(listID)
		

def renameList(args, tasklists):
	origList = args[0]
	newList = args[1]
	for tasklist in tasklists['items']:
		if tasklist['title'] == origList:
			tasklist['title'] = newList
			result = service.tasklists().update(tasklist=tasklist['id'], body=tasklist).execute()
			print origList+' renamed '+newList
			break

def delList(args, tasklists):
	listName = args
	for tasklist in tasklists['items']:
		if tasklist['title'] == listName[0]:
			service.tasklists().delete(tasklist=tasklist['id']).execute()
			print listName, " deleted!"
			break		

def newTask(args, tasklists):
	listName = args[0]
#	dueDate = ''
	if len(args) > 2:
#		if args[2] == 'today':
#			dueDate = today.strftime('%Y-%m-%d')
#		elif args[2] == 'tomorrow':
#			dueDate = tomorrow.strftime('%Y-%m-%d')
#		elif args[2] == 'next week':
#			dueDate = nextWeek.strftime('%Y-%m-%d')
#		elif args[2] == '2 weeks':
#			dueDate = twoWeeks.strftime('%Y-%m-%d')
#		elif args[2] == 'next month':
#			dueDate = nextMonth.strftime('%Y-%m-%d')
#		else: dueDate = args[2]
#		convertDue = dueDate+'T12:00:00.000Z'
		convertDue = dueDate(args[2])
		task = {
	 		'title': args[1], 
	 		'due': convertDue,
			}
	else:
		task = {
			'title': args[1]
			}					
	listID = None
	for tasklist in tasklists['items']:
		if listName == tasklist['title']:
			listID=tasklist['id']
			break
	if listID == None:
		tasklist = {
	  	'title': listName,
	  	}
		result = service.tasklists().insert(body=tasklist).execute()
		listID = result['id']				
	newTask = service.tasks().insert(tasklist=listID, body=task).execute()
	print 'Completed.'

def clearTask(tasklists):
	for tasklist in tasklists['items']:
		listID = tasklist['id']
		#service.tasks().clear(tasklist=listID, body='').execute()
		service.tasks().clear(tasklist=listID).execute()
	print 'Cleared.'

def delTask(args, tasklists):
	listName= args[0]
	taskNumber = int(args[1])
    # match list off of list name
	listID = None
	for tasklist in tasklists['items']:
		if listName == tasklist['title']:
			listID=tasklist['id']
			break			
    # select and delete task
	tasks = service.tasks().list(tasklist=listID).execute()
	newList = tasks['items']
	selectTask = newList[taskNumber-1]
	taskID = selectTask['id']
	service.tasks().delete(tasklist=listID, task=taskID).execute()
	print "Completed."

def updateTask(args, tasklists):
	listName = args[0]
	taskNumber = int(args[1])		
	for tasklist in tasklists['items']:
		if listName == tasklist['title']:
			listID=tasklist['id']
			break
	tasks = service.tasks().list(tasklist=listID).execute()
	newList = tasks['items']
	selectTask = newList[taskNumber-1]
	taskID = selectTask['id']	
	chooseTask = service.tasks().get(tasklist=listID, task=taskID).execute()
	chooseTask['status'] = 'completed'
	markIt = service.tasks().update(tasklist=listID, task=chooseTask['id'], body=chooseTask).execute()
	print "Completed"

def naturalDate(string):
    '''Takes a string in natural language form and returns a date'''
    pass

relDays = {'today':today, 'tomorrow':tomorrow, 'nextWeek': nextWeek, 'nextMonth':nextMonth}

weekdays = {'mon':0, 'tue':1, 'wed':2, 'thu':3, 'fri':4, 'sat':5, 'sun':6, 'monday' : 0, 'tuesday':1, 'wednesday':2,'thursday':3, 'friday':4, 'saturday':5, 'sunday':6 }

todayDate = datetime.date.today()

def ConfigSectionMap(section):
    dict1 = {}
    Config = ConfigParser.ConfigParser()
    try:
        Config.read('api.cfg')
    except:
        print "Cannot read file"
        return dict1
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


def validate():
#print ConfigSectionMap("API")

    FLAGS = gflags.FLAGS

# Set up a Flow object to be used if we need to authenticate. This
# sample uses OAuth 2.0, and we set up the OAuth2WebServerFlow with
# the information it needs to authenticate. Note that it is called
# the Web Server Flow, but it can also handle the flow for native
# applications
# The client_id and client_secret are copied from the API Access tab on
# the Google APIs Console
    FLOW = OAuth2WebServerFlow(
        client_id = ConfigSectionMap("API")['clientid'],
        client_secret = ConfigSectionMap("API")['clientsecret'],
        scope = 'https://www.googleapis.com/auth/tasks',
        user_agent = 'pytasks')

# To disable the local server feature, uncomment the following line:
    FLAGS.auth_local_webserver = False

# If the Credentials don't exist or are invalid, run through the native client
# flow. The Storage object will ensure that if successful the good
# Credentials will get written back to a file.

    taskStore = "tasks.dat"
    storage = Storage(taskStore)
    credentials = storage.get()
    if credentials is None or credentials.invalid == True:
        try:
            credentials = run(FLOW, storage)
        except KeyboardInterrupt:
            print "Aborting."

# Create an httplib2.Http object to handle our HTTP requests and authorize it
# with our good Credentials.
    http = httplib2.Http(cache=".cache")
    http = credentials.authorize(http)


# Build a service object for interacting with the API. Visit
# the Google APIs Console
# to get a developerKey for your own application.
    service = build(serviceName='tasks', version='v1', http=http,
           developerKey = ConfigSectionMap("API")['developerkey'])
           #developerKey=keyring.get_password('XXXXXXXXX', 'XXXXXXXXX'))

if __name__ == "__main__":
    # validate_cfg()
    # authorize_connection()

#           Running the program with no arguments should list tasks form all task lists
# -l        list a single task list
# -a     add a task to "Main"
# -a -l     add a task to specific list
# -x        toggle mark task as completed
# -x -l     toggle mark task as completed (search within single list)
# -d [-l]   delete task
# -C [-l]   Clear completed tasks
# -A     add new task list
# -D        delete task list

    parser = argparse.ArgumentParser(usage="tasks [option] arg1 arg2 arg3", prog="pytasks")

    parser.add_argument('-l', '--list', nargs='*', action='append',
            help='Lists tasks. For a sinlge list, pass the list name.')

    parser.add_argument('-a', '--add', nargs='+',  action='append',
            help='Adds new task.')

    parser.add_argument('-x', '--complete', nargs='+', action='append',
            help='Marks a task as completed. Pass the \
            name of the list and the number of the task. The number is available by first listing tasks \
            with the -l command. For example: tasks -u Main 1. This command would mark the first message \
            on the Main list as completed.')

    parser.add_argument('-d', '--delete', nargs='+', action='append', 
            help='Deletes a designated task.')

    
    parser.add_argument('-L', '--List', nargs='*', action='append', 
            help='Lists task lists.')

    parser.add_argument('-C', '--clear', nargs='?', action='append', const=True, default=False,
            help='Clears completed tasks from your lists. Optionally from a single list.')
    
    parser.add_argument('-A', '--New', nargs='+', action='append', 
            help='Create new task list.') 

    parser.add_argument('-D', '--Delete', nargs='+', action='append',
            help='Delete a task list.')


    #tasklists = service.tasklists().list().execute()
    args = parser.parse_args()
    args = vars(args)
    
    for key in args:
        try:
            args[key] = [' '.join(x) for x in args[key]]
        except:
            pass

#    if args['add']:
#       add_tasks(args['add'], args['list'])

#    if args.new != None:
#        newTask(args.new, tasklists)
#    elif args.clear == True:
#        clearTask(tasklists)
#    elif args.update != None:
#        updateTask(args.update, tasklists)
#    elif args.delTask != None: 
#        delTask(args.delTask, tasklists)
#    elif args.newList != None:
#        renameList(args.newList, tasklists)
#    elif args.delList != None:
#        delList(args.delList, tasklists)
#    elif args.tList != None: 
#        listTasks(args.tList, tasklists)



