#!/usr/bin/python3

import boto3
import botocore
import requests
import os
from datetime import *
import urllib3
import json
import configparser
import random

config = configparser.ConfigParser()
config.read('gophish.ini')

userpath = config['localsys']['userpath']
availabilityzone = config['aws']['availabilityzone']
securitygroup = config['aws']['securitygroup']
instanceid = config['aws']['instanceid']
elbprefix = config['aws']['elbprefix']
gophishapikey = config['gophish']['gophishapikey']
campaigndays = config['gophish']['campaigndays']
elb_remove_date_tag = config['gophish']['elb_remove_date_tag']
gophishurl = config['gophish']['gophishurl']
groupprefix = config['gophish']['groupprefix']


client = boto3.client('elb')
urllib3.disable_warnings()

#Datetime objects
class Time:
    def __init__(self):
        self.new_time = datetime.now().astimezone().replace(microsecond=0) + timedelta(minutes=1)
        self.send_now = self.new_time.isoformat()
        self.elb_remove_date_time = date.today() + timedelta(days=int(elb_remove_date_tag))
        self.elb_date_str = self.elb_remove_date_time.strftime("%Y-%m-%d")
        self.today = datetime.today()
        self.amount_days = timedelta(int(campaigndays))
        self.add_days = self.new_time + self.amount_days
        self.send_by = self.add_days.isoformat()

# This function returns an object of Time
def ret():
    return Time()

time = ret()

def count_files():
    initial_count = 0
    for path in os.listdir(userpath):
        if os.path.isfile(os.path.join(userpath, path)):
            initial_count += 1
    return initial_count


#Creates ELBs and returns ELB names
def create_elbs(elbpref, initial_count):
    elbnames = []
    for i in range(1, int(initial_count) + 1):
        elbname = elbpref + "-" + str(i)
        response = client.create_load_balancer(
            LoadBalancerName=elbname,
            Listeners=[
                {
                    'Protocol': 'HTTP',
                    'LoadBalancerPort': 80,
                    'InstanceProtocol': 'HTTP',
                    'InstancePort': 80
                },
            ],
            AvailabilityZones=[
                availabilityzone,
            ],
            SecurityGroups=[
                securitygroup,
            ],
            Scheme='internet-facing',
            Tags=[
                {
                    'Key': 'owner',
                    'Value': 'secops',
                    'Key':   'date to remove',
                    'Value': str(time.elb_date_str)
                },
            ]
        )
        elbnames.append(response['DNSName'])
        response = client.register_instances_with_load_balancer(
            LoadBalancerName=elbname,
            Instances=[
                {
                    'InstanceId': instanceid
                },
            ]
        )
    elbnames = ["http://" + sub for sub in elbnames]
    return elbnames

#Grabs local csv and creates gophish user groups, returns group name
def convertcreate_group(files, groupprefix):
    gophishgrpname = []
    try:
        files = os.listdir(userpath)
        for csv in files:
            headers = {'Authorization': 'Bearer '+ gophishapikey,}
            files = {
                'file': (userpath + csv, open(userpath + csv, 'rb')),
            }
            response = requests.post(gophishurl + '/api/import/group',
                                        headers=headers, files=files, verify=False)
            responseusers = response.text
            targets = json.loads(responseusers)
            headers = {
                'Authorization': 'Bearer '+ gophishapikey,
                'Content-Type': 'application/json',
                }
            data = {"name": groupprefix + csv, "targets": targets}
            jsondata = json.dumps(data)
            response = requests.post(gophishurl + '/api/groups/', headers=headers, data=jsondata, verify=False)
            responsebody = response.content
            gophishresp = json.loads(responsebody.decode('utf-8'))
            gophishgrpname.append(gophishresp['name'])
    except KeyError:
        print("Error: Groups already exist") 
    return gophishgrpname

#creates dictionary with gophish group IDs and ELB urls
def create_dict(group, diction):
    elbgodict = dict(zip(group, diction)) 
    return elbgodict


# Get random template
def get_temp():
    headers = {'Authorization': 'Bearer '+ gophishapikey,}
    response = requests.get(gophishurl + '/api/templates/', headers=headers, verify=False)
    responsebody = response.content
    responsedecode = json.loads(responsebody.decode('utf-8'))
    templist = []
    for i in responsedecode:
        for key, value in i.items():
            if key == 'name':
                templist.append(value)
    random_tmp = random.choice(templist)
    return random_tmp

#Get random page
def get_page():
    headers = {'Authorization': 'Bearer '+ gophishapikey,}
    response = requests.get(gophishurl + '/api/pages/', headers=headers, verify=False)
    responsebody = response.content
    responsedecode = json.loads(responsebody.decode('utf-8'))
    pagelist = []
    for i in responsedecode:
        for key, value in i.items():
            if key == 'name':
                pagelist.append(value)
    random_pg = random.choice(pagelist)
    return random_pg


#Creates campaign
def create_campaign(sendby, sendnow, elbgodict,random_tmp, random_pg):
    if not elbgodict:
        print("Error: Gophish and/or ELB names not collected")
    else:
        headers = {'Authorization': 'Bearer '+ gophishapikey,}
        for groups,elbs in elbgodict.items():
            data = {
                "name": groups,
                "template": {"name": random_tmp},
                "url": elbs,
                "page": {"name": random_pg},
                "smtp": {"name": "DWteams@outlook.com"},
                "launch_date": str(sendnow),
                "send_by_date": str(sendby),
                "groups": [{"name": groups}]
                    }
            jsondata = json.dumps(data)
            response = requests.post(gophishurl + '/api/campaigns/', headers=headers, data=jsondata, verify=False)
            responsebody = response.content
            responsedecode = json.loads(responsebody.decode('utf-8'))

#Main function
def main():
    numberoffiles = count_files()
    if not os.listdir(userpath) :
        print("No user groups found in specified directory")
        return False
    else:
        files = os.listdir(userpath)
    random_tmp = get_temp()
    random_pg = get_page()
    gophishgroupname = convertcreate_group(files, groupprefix)
    elboutput = create_elbs(elbprefix, numberoffiles)
    elbgodict = create_dict(gophishgroupname, elboutput)
    startcampagin = create_campaign(time.send_by, time.send_now, elbgodict, random_tmp, random_pg)
main()
