#!/usr/bin/python3

import boto3
import requests
import os
from datetime import *
import urllib3
import json
import configparser

#Import from config
config = configparser.ConfigParser()
config.read('gophish.ini')
userpath = config['localpath']['userpath']
gophishapikey = config['gophish']['gophishapikey']
availabilityzone = config['aws']['availabilityzone']
securitygroup = config['aws']['securitygroup']
instanceid = config['aws']['instanceid']
campaigndays = config['gophish']['campaigndays']
gophishurl = config['gophish']['gophishurl']
elbprefix = config['aws']['elbprefix']
groupprefix = config['gophish']['groupprefix']
delaydays = config['gophish']['delaydays']
headers = {'Authorization': 'Bearer '+ gophishapikey,}

#Datime objects
class Time:
    def __init__(self):
        self.today = datetime.today().strftime('%Y-%m-%d')
        self.year = date.today().strftime('%Y')
        self.datenow = datetime.now()
        self.date_today = self.d.date()
        self.today = datetime.today()
        self.delay = timedelta(days=int(delaydays))
  
# This function returns an object of Time
def ret():
    return Time()

time = ret() 

"""
today = datetime.today().strftime('%Y-%m-%d')
year = date.today().strftime('%Y')
d = datetime.now()
date_today = d.date()
new_time = datetime.now().astimezone().replace(microsecond=0) + timedelta(hours=1)
amount_days = timedelta(int(campaigndays))
add_days = new_time + amount_days
send_by = add_days.isoformat()
delay = timedelta(days=int(delaydays))
"""
urllib3.disable_warnings()

#Get Gophish Campagin ID
def get_campaginid():
    id_list = []
    response = requests.get(gophishurl + '/api/campaigns/', headers=headers, verify=False)
    responsebody = response.content
    responsedecode = json.loads(responsebody.decode('utf-8'))
    for i in responsedecode:
        id_list.append(i['id'])
    return id_list

#Get GoPhish Campagin status 
def get_campaginstatus(id_list):
    datelist = []
    dateform = []
    campaginid = []
    formatted_id_dict = {}
    for campaign in id_list:
        response = requests.get(gophishurl + '/api/campaigns/'+ str(campaign) + '/summary', headers=headers, verify=False)
        responsebody = response.content
        responsedecode = json.loads(responsebody.decode('utf-8'))
        if responsedecode['status'] == 'In progress':
            datelist.append(responsedecode['send_by_date'])
            campaginid.append(responsedecode['id'])
        else:
            continue
    for dateformat in datelist:
        dateformat = dateformat[:10]
        dateformatted = datetime.strptime(dateformat, "%Y-%m-%d")
        dateform.append(dateformatted)
    for key in campaginid:
        for value in dateform:
            formatted_id_dict[key] = value
            break
    return formatted_id_dict, dateform

#End Gophish campagin ID
def end_campagin(formatted_id_dict, dateform):
    end_id = []
    end_campagin_id = []
    for key, value in formatted_id_dict.items():
        enddate = time.datenow + time.delay
        if enddate >= value:
            end_campagin_id.append(key)
            continue  
        else:
            return False
    if not end_campagin_id:
        return False
    else:
        for ending in end_campagin_id:
            response = requests.get(gophishurl + '/api/campaigns/'+ str(ending)+'/complete', headers=headers, verify=False)
            responsebody = response.content
        return True

#Get AWS ELB 
def get_elb():
    elbnames = []
    dnsnames = []
    client = boto3.client('elb')
    response = client.describe_load_balancers()
    elbnames.append(response['LoadBalancerDescriptions'])
    for names in elbnames:
        for name in names:
            for key,value in name.items():
                if key == 'LoadBalancerName':
                    dnsnames.append(value) 
    return dnsnames

#Remove AWS ELB
def remove_elb(dnsnames):
    if dnsnames == []:
        pass
    else:
        client = boto3.client('elb')                            
        for elbs in dnsnames:
            response = client.delete_load_balancer(
            LoadBalancerName=
                elbs,
        )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True

#Remove Gophish usergroup    
def remove_usergrp():
    groupidlst = []
    response = requests.get(config['gophish']['gophishurl'] + '/api/groups/', headers=headers, verify=False)
    responsebody = response.content
    responsedecode = json.loads(responsebody.decode('utf-8'))
    for usergrp in responsedecode:
        for key,value in usergrp.items():
            if 'name' in key:
                if groupprefix in value:
                    groupid = usergrp.get("id")
                    groupidlst.append(groupid)
                else:
                    pass
    for groups in groupidlst:
        response = requests.delete(gophishurl + '/api/groups/' + str(groups), headers=headers, verify=False)
        responsebody = response.content

def main():
    get_campagin = get_campaginid()
    formatted_id_dict, dateform = get_campaginstatus(get_campagin)
    end_camp = end_campagin(formatted_id_dict, dateform)
    getelb = get_elb()
    if end_camp == True:
        rm_elb = remove_elb(getelb)
        if rm_elb == True:
            rm_grp = remove_usergrp()
    else:
        pass
main()