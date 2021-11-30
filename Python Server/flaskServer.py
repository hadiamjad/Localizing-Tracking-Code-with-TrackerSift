# import statements
import pandas as pd
import numpy as np
import ast
import os
import json
import math
import requests
import time
import tldextract
import traceback
import xlsxwriter
from urllib.parse import urlparse
from adblockparser import AdblockRules
from flask import Flask, request, abort, jsonify
from flask_cors import CORS

# server-client basic setup
app = Flask(__name__)
CORS(app)

# helper functions
def write_json(new_data, filename='data.json'):
   
    with open(filename,'r+') as file:
         # First we load existing data into a dict.
         file_data = json.load(file)
         # Join new_data with file_data inside emp_details
         file_data.append(new_data)
         # Sets file's current position at offset.
         file.seek(0)
         # convert back to json.
         json.dump(file_data, file, indent = 4)

def getHostname(url):
    return urlparse(url).netloc

def initiatorScriptMethod(callstack, flag):
    if flag == 0:
        if callstack['type'] != 'script': return None

        for item in callstack['stack']['callFrames']:
            return item['url'] +"@"+ item['functionName']+"@"+ str(item['lineNumber'])+"@"+ str(item['columnNumber'])
    else:
        for item in callstack['callFrames']:
            return item['url'] +"@"+ item['functionName']+"@"+ str(item['lineNumber'])+"@"+ str(item['columnNumber'])

    return initiatorScript(callstack['stack']['parent'], 1)

def initiatorScript(callstack, flag):
    if flag == 0:
        if callstack['type'] != 'script': return None

        for item in callstack['stack']['callFrames']:
            return item['url']
    else:
        for item in callstack['callFrames']:
            return item['url']

    return initiatorScript(callstack['stack']['parent'], 1)

def getScript(initiatorScriptMethod):
    word = initiatorScriptMethod.split('@')
    return word[0] + "@" +word[1]

# Classification phase
# dic == domain level classification of the page
# dic2 == hostname level classification of the page
# dic3 == script level classification of the page
# dic 4 == statement level classification
def DistGraphPlotter(dataset, dic, dic2, dic3, dic4):  
    # domain and hostname level classification
    # iterating complete dataset
    for i in dataset.index:
      # handling non-script type
      if dataset['call_stack'][i]['type'] != 'script': pass
      else:
                  domkey = getDomain(dataset['http_req'][i])
                  hostkey = getHostname(dataset['http_req'][i])

                  # inserting domainkey as a new pair
                  if domkey not in dic.keys():
                      dic[domkey] = [0, 0, [], []]
                  # checking tracking and non-tracking calls
                  if dataset['easylistflag'][i] == 1 or dataset['easyprivacylistflag'][i] == 1 or dataset['ancestorflag'][i] == 1:
                      dic[domkey][0] += 1
                      if getHostname(dataset['http_req'][i]) not in dic[domkey][2]:
                        dic[domkey][2].append(getHostname(dataset['http_req'][i]))
                  else:
                      dic[domkey][1] += 1
                      if getHostname(dataset['http_req'][i]) not in dic[domkey][3]:
                        dic[domkey][3].append(getHostname(dataset['http_req'][i]))

                  # inserting hostnamekey as a new pair
                  if hostkey not in dic2.keys():
                      dic2[hostkey] = [0, 0]

                  if dataset['easylistflag'][i] == 1 or dataset['easyprivacylistflag'][i] == 1 or dataset['ancestorflag'][i] == 1:
                      dic2[hostkey][0] += 1
                  else:
                      dic2[hostkey][1] += 1
    
    # initiator script and method level classification
    # iterating complete dataset
    #dataset['initatorscript'] = dataset.apply(lambda row: initiatorScript(row.call_stack, 0), axis=1)
    #dataset['initatorscriptMethod'] = dataset.apply(lambda row: initiatorScriptMethod(row.call_stack, 0), axis=1)
    for i in dataset.index:
            # handling non-script type
            if dataset['call_stack'][i]['type'] != 'script': pass
            else:   
                #scriptkey = dataset['top_level_url'][i]+"@"+dataset['initatorscript'][i]
                #scriptmethodkey = dataset['top_level_url'][i]+"@"+dataset['initatorscriptMethod'][i]
                # unique scripts and method in the stack
                unique_scripts = []
                unique_scripts_method = []
                # recursively insert unique scripts in the stack
                rec_stack_checker(dataset['call_stack'][i]['stack'], unique_scripts)
                # recursively insert unique scripts methods in the stack
                rec_stack_checker_method(dataset['call_stack'][i]['stack'], unique_scripts_method)

                for j in range(len(unique_scripts)):
                    scriptkey = unique_scripts[j]

                    # inserting script as a new pair
                    if scriptkey not in dic3.keys():
                        dic3[scriptkey] = [0, 0, [], []]

                    if dataset['easylistflag'][i] == 1 or dataset['easyprivacylistflag'][i] == 1 or dataset['ancestorflag'][i] == 1:
                        dic3[scriptkey][0] += 1
                        dic3[scriptkey][2].append(dataset['http_req'][i])
                    else:
                        dic3[scriptkey][1] += 1
                        dic3[scriptkey][3].append(dataset['http_req'][i])

                for j in range(len(unique_scripts_method)):
                    scriptmthodkey = unique_scripts_method[j]

                    # inserting scriptmethod as a new pair
                    if scriptmthodkey not in dic4.keys():
                        dic4[scriptmthodkey] = [0, 0, [], []]

                    if dataset['easylistflag'][i] == 1 or dataset['easyprivacylistflag'][i] == 1 or dataset['ancestorflag'][i] == 1:
                        dic4[scriptmthodkey][0] += 1
                        dic4[scriptmthodkey][2].append(dataset['http_req'][i])
                    else:
                        dic4[scriptmthodkey][1] += 1
                        dic4[scriptmthodkey][3].append(dataset['http_req'][i])


"""#### EasyList & EasyPrivacyList
- update the EasyList and EasyPrivacyList file paths

`CheckTrackingReq(rules, url, top_level_url, resource_type)`
"""
# Description: append the filter rules list
# input: filename = file containing easylist and easyprivacylist
# return: Adblock rules object
def getRules(filename):
    df = pd.read_excel(filename)
    rules = []
    for i in df.index:
        rules.append(df['url'][i])
    Rules = AdblockRules(rules)
    return Rules

# Description: setting predefined rules
easylist = getRules('EasyPrivacyList.xlsx')
easyPrivacylist = getRules('easyList.xlsx')

# Description: extract domain from given url
# input: url = url for which domain is needed
# return: domain
def getDomain(url):
    ext = tldextract.extract(url)
    return ext.domain+"."+ext.suffix

# Description: check if its thirparty request
# input: url = url
# input: top_level_url = top_level_url
# return: returns True if its thirdparty request otherwise false
def isThirdPartyReq(url, top_level_url):
    d_url = getDomain(url)
    d_top_level_url = getDomain(top_level_url)
    if d_url == d_top_level_url:
        return False
    else:
        return True

# Description: check if the request is tracking or non-tracking
# input: rules = Adblock rules object
# input: url = url
# input: top_level_url = top_level_url
# input: resource_type = resource_type
# return: returns True if it has tracking status otherwise false
def CheckTrackingReq(rules, url, top_level_url, resource_type):
    return int(rules.should_block(url, { resource_type: resource_type, 'domain' : getDomain(url), 'third-party': isThirdPartyReq(url, top_level_url) }))

"""#### Check Ancestor Nodes for Tracking Behavior
`CheckAncestoralNodes(df, row.call_stack)`

`callstack` -> `stack` & `type`='Script' -> `callframes` & `parent`

"""
# Description: Search the tracking status for each unique script url's in the stack
# input: dataset = complete http_req table with easylist and easyprivacylist flags
# input: callstack = call stack object as shown above
# return: it returns 1 if any ancestoral node has tracking status otherwise 0
def CheckAncestoralNodes(dataset,callstack):
  # handling non-script type
  if callstack['type'] != 'script': return None
  # unique scripts in the stack
  unique_scripts = []
  # recursively insert unique scripts in the stack
  rec_stack_checker(callstack["stack"], unique_scripts)
  # check the tracking status of the unique scripts
  return check_script_url(dataset, unique_scripts)

# Description: Search the tracking status for each unique script url's in the stack
# input: dataset = complete http_req table with easylist and easyprivacylist flags
# input: unique_scripts = unique scripts in the given stack
# return: it returns 1 if any unique script url has tracking status otherwise 0
def check_script_url(dataset, unique_scripts):
  for i in range(len(unique_scripts)):
    for j in dataset.index:
      if dataset['http_req'][j] == unique_scripts[i]:
        if dataset['easylistflag'][j] == 1 or dataset['easyprivacylistflag'][j] == 1: return 1
  return 0


# Description: it appends the unique script url's recursively
# input: stack = stack object as shown in the image above
# input: unique_scripts = unique scripts in the given stack
# return: nothing
def rec_stack_checker(stack, unique_scripts):
  # append unique script_url's
  for item in stack['callFrames']:
    if item['url'] not in unique_scripts:
      unique_scripts.append(item['url'])
  # if parent object doen't exist return (base-case)
  if 'parent' not in stack.keys(): return
  # else send a recursive call for this
  else: rec_stack_checker(stack['parent'], unique_scripts)

# Description: it appends the unique script url, method, lineNo, columnNo recursively
# input: stack = stack object as shown in the image above
# input: unique_scripts_method = unique scripts with complete lineNo info in the given stack
# return: nothing
def rec_stack_checker_method(stack, unique_scripts_methods):
  # append unique script_url's
  for item in stack['callFrames']:
    # if item['url']+"@"+ item['functionName']+"@"+ str(item['lineNumber'])+"@"+ str(item['columnNumber']) not in unique_scripts_methods:
    #   unique_scripts_methods.append(item['url']+"@"+ item['functionName']+"@"+ str(item['lineNumber'])+"@"+ str(item['columnNumber']))
    if item['url']+"@"+ item['functionName'] not in unique_scripts_methods:
      unique_scripts_methods.append(item['url']+"@"+ item['functionName'])
  # if parent object doen't exist return (base-case)
  if 'parent' not in stack.keys(): return
  # else send a recursive call for this
  else: rec_stack_checker(stack['parent'], unique_scripts_methods)



"""### DataFrame to Excel
`df_to_excel(dataset, 'test.xlsx')`

"""
# Description: Converts dataframe to excel file
# input: dataset = dataframe to be converted
# input: filename = name of the csv file 'test.xlsx'
# return: nothing
def df_to_excel(dataset, filename):
  writer = pd.ExcelWriter(filename, engine='xlsxwriter',options={'strings_to_urls': False})
  dataset.to_excel(writer)
  writer.close()

"""#### Intilization
Pass complete dataset and it will add columns for:
- EasyList
- EasyPrivacyList
- AncestorFlag

All of these are boolean(0/1) flags where:
- 0 means non-tracking status
- 1 means tracking status

`df = intilization('/output.json')`
"""
# Labelling phase
# Description: Handles all initilization process like EasyList, EasyPrivacyList, Ancestor Flags
# return: returns updated dataframe
def intilization(dataset, complete_dataset):
            retDataset = pd.DataFrame()
            # adding easylistflag column
            dataset['easylistflag'] = dataset.apply(
                lambda row: CheckTrackingReq(easylist, row.http_req, row.frame_url, row.resource_type), axis=1)

            # adding easyprivacylistflag column
            dataset['easyprivacylistflag'] = dataset.apply(
                lambda row: CheckTrackingReq(easyPrivacylist, row.http_req, row.frame_url, row.resource_type), axis=1)
            
            dataset["ancestorflag"] = dataset.apply(lambda row: CheckAncestoralNodes(complete_dataset, row.call_stack), axis=1)
            retDataset = retDataset.append(dataset)
            return retDataset

# Creating check boxes for the tracking requests for front end
def getTracking(dataset, domain, hostname, script, scriptstmt):
    retReq = {}
    for i in dataset.index:
      # handling non-script type
      if dataset['call_stack'][i]['type'] != 'script': pass
      else:
        if dataset['easylistflag'][i] == 1 or dataset['easyprivacylistflag'][i] == 1 or dataset['ancestorflag'][i] == 1:
            dom = getDomain(dataset['http_req'][i])
            hstname = getHostname(dataset['http_req'][i])
            try:
                if domain[dom][1] == 0:
                    if dom not in retReq.keys():
                        retReq[dom] = [[],"Domain"]
                    if dataset['http_req'][i] not in retReq[dom][0]:
                        retReq[dom][0].append(dataset['http_req'][i])
                elif hostname[hstname][1] == 0:
                    if hstname not in retReq.keys():
                        retReq[hstname] = [[],"Hostname"]
                    if dataset['http_req'][i] not in retReq[hstname][0]:
                        retReq[hstname][0].append(dataset['http_req'][i])
                else:
                    flag = 0
                    # unique scripts in the stack
                    unique_scripts = []
                    # recursively insert unique scripts in the stack
                    rec_stack_checker(dataset['call_stack'][i]['stack'], unique_scripts)
                    for j in range(len(unique_scripts)):
                        if script[unique_scripts[j]][1] == 0:
                            if unique_scripts[j] not in retReq.keys():
                                retReq[unique_scripts[j]] = [[],"Script"]
                            if dataset['http_req'][i] not in retReq[unique_scripts[j]][0]:
                                retReq[unique_scripts[j]][0].append(dataset['http_req'][i])
                            flag = 1
                            break
                    
                    if flag == 0:
                        # unique scripts stmts in the stack
                        unique_scriptsstmts = []
                        # recursively insert unique scripts methods in the stack
                        rec_stack_checker_method(dataset['call_stack'][i]['stack'], unique_scriptsstmts)
                        for j in range(len(unique_scriptsstmts)):
                            if scriptstmt[unique_scriptsstmts[j]][1] == 0:
                                if unique_scriptsstmts[j] not in retReq.keys():
                                    retReq[unique_scriptsstmts[j]] = [[],"Method"]
                                if dataset['http_req'][i] not in retReq[unique_scriptsstmts[j]][0]:
                                    retReq[unique_scriptsstmts[j]][0].append(dataset['http_req'][i])
                                break 
            except:
                pass
    return retReq

# Client post request handler logic
reqs = pd.DataFrame()
resp = pd.DataFrame()
domain = {}
hostname = {}
script = {}
scriptstmt = {}


@app.route('/request', methods=["POST"])
def request_handler():
    lst = []
    lst.append((request.json['http_req'], request.json['call_stack'], request.json['resource_type'], request.json['top_level_url'], request.json['frame_url'], request.json['request_id']))
    df = pd.DataFrame(lst, columns=['http_req', 'call_stack', 'resource_type', 'top_level_url', 'frame_url', 'request_id'])
    global reqs
    df = intilization(df, reqs)
    reqs = reqs.append(df, ignore_index=True)
    #reqs.to_csv(r'label.csv')
    DistGraphPlotter(df, domain, hostname, script, scriptstmt)
    df2 = pd.DataFrame.from_dict(domain)
    #df2.to_csv(r'domain.csv')
    df2 = pd.DataFrame.from_dict(hostname)
    #df2.to_csv(r'hostname.csv')
    df2 = pd.DataFrame.from_dict(script)
    #df2.to_csv(r'script.csv')
    df2 = pd.DataFrame.from_dict(scriptstmt)
    #df2.to_csv(r'scriptstmt.csv')
    retReq = getTracking(reqs, domain, hostname, script, scriptstmt)

    return jsonify(retReq), 200

@app.route('/response', methods=["POST"])
def response_handler():
    try:
        lst = []
        lst.append((request.json['response_body'], request.json['response'], request.json['request_id']))
        df = pd.DataFrame(lst, columns=['response_body', 'response', 'request_id'])
        global resp
        reqs = resp.append(df, ignore_index=True)
        #reqs.to_json(r'resp.json')
        df_to_excel(reqs, r'resp.xlsx')
    except:
        pass

    return jsonify({'sucess': 200}), 200

@app.route('/reload', methods=["GET"])
def reload_handler():
    global reqs
    reqs = pd.DataFrame()
    return {'status': 200}

app.run(debug=True)