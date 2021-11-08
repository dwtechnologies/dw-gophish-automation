# dw-gophish-automation


## Table of contents
* [General info](#general-info)
* [Technologies](#technologies)
* [Setup](#setup)

## General info
This project is intended to automate the procedure internal phishing campaigns via Gophish as well as avoiding the GoPhish URL being flagged by google safebrowsing. The idea is to run it completely by itself by scheduling the scripts to run in the prefered manner. This means all GoPhish campagin settings such as templates or landing pages should be considered in production since the script will choose from them randomly. We have found the sweetspot to avoid google safebrowsing is to send out 250-300 users over 21 days. This is intended for orgranizations with 1000-2000 users but can be adjusted for larger organizations. This has been run and tested using crontab to run start script, stop script, and getuser.sh and using task scheduler in windows to run getusergroups.ps1 to keep your userlist updated.



**getusergroups.ps1**
	- Powershell script to get enabled users from active directory, split them randomly to 5 different CSV files in the gophish format and upload them to an s3 bucket. Schedule to run weekly (modify this script if you have more than 2000 users)

**getusers.sh**
	- Shell script to download userslist CSV's to Gophish instance. Schedule to run daily.
	
**gophish.ini**
	- Config file

**gophishautomationstart.py**
	- Start file. Schedule to run on prefered intervall or run manually.

**gophishautomationstop.py** 
	- Stop file. Schedule to run daily.

### A few things to remember


1. Userlist - You need to supply CSVs in the acceptable GoPhish format (https://docs.getgophish.com/user-guide/building-your-first-campaign/importing-groups). A powershell script is included to export userlists and upload them to an S3 bucket.
2. AWS Permissions - We use several AWS services such as S3, VPC, and IAM. You will need....
   - S3: GetBucket, PutObject, ListBucket
   - elasticloadbalancing: DescribeLoadBalancers, DeleteLoadBalancer, CreateLoadBalancer, AddTags, SetSecurityGroups, RegisterTargets, ModifyListener
3. Config
   - getusers.sh: specify s3 bucket path. 
   - getusergroups.ps1 : specify OU, paths, S3 bucket path.
   - gophish.ini : specify everything.
  
![diagram](https://user-images.githubusercontent.com/70007848/136763087-70a5387b-534f-4679-a1dd-4e6ace94b40a.png)  
  
## Technologies
Project is created with:
* Python 3.9.5
* Powershell 7.0
* Boto3

## Setup
To run this project, clone repo, install dependencies, change config, run:

```
$ git clone https://github.com/dwtechnologies/gophishautomation.git
$ install depenedencies
$ change config (gophish.ini,getusers.sh,getusers.sh)
```

