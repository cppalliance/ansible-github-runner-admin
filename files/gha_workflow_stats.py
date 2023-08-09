#!/usr/bin/python3

# Script to collect prometheus statistics about github actions, and adjust self-hosted runners.
# Instructions:
# Install gh. "apt install gh". Run it and login.
# Set up a cron job, for example every 30 minutes.
# */30 * * * * /root/scripts/gha_workflow_stats.py > /var/lib/node_exporter/gha_workflow_stats.prom.$$ && mv /var/lib/node_exporter/gha_workflow_stats.prom.$$ /var/lib/node_exporter/gha_workflow_stats.prom

import subprocess
import json
import os
import sys
import shutil
import datetime
import gha_workflow_stats_config_data as config_data
from collections import defaultdict

ct = datetime.datetime.now()

debuglog = open("/tmp/gha_workflow_stats_log", "w")
debuglog.write("Starting: " + str(ct) + " ")
debuglog.flush()

querycount="2000"
allresults={}

def def_value():
    return 0

os.environ['GH_TOKEN'] = config_data.gh_token
x = subprocess.run(['gh', 'auth', 'status'], stdout=subprocess.PIPE, stderr = subprocess.STDOUT)
result=x.stdout.decode('UTF-8')
debuglog.write(result)
debuglog.flush()

# Discover list of all repos
allrepos = subprocess.run(['gh', 'repo', 'list', config_data.gh_organization, '-L', querycount, '--json', 'name', '--jq', '.[].name'], stdout=subprocess.PIPE)

statuslist=["in_progress", "queued", "requested", "waiting", "pending"]
for status in statuslist:
    allresults[status]=0

for x in allrepos.stdout.splitlines():
    repo = x.decode('UTF-8')
    # print("repo is " + repo)
    for status in statuslist:
        x = subprocess.run(['gh', 'api', "repos/" + config_data.gh_organization + "/" + repo + "/actions/runs?status=" + status], stdout=subprocess.PIPE)
        result=x.stdout.decode('UTF-8')
        data = json.loads(result)
        # print("RESULT FOR " + status + " is:" + str(data["total_count"]))
        allresults[status]=allresults[status] + data["total_count"]
        if int(data["total_count"]) > 0:
            debuglog.write(repo + " " + status + " " + str(data['total_count']) + " \n")
            debuglog.flush()
        
# Completed
# print(allresults)
for status in statuslist:
    print("gha_wf_status{owner=\"" + config_data.gh_organization + "\", status_type=\"" + status + "\"} " + str(allresults[status]))

# BILLING DATA COLLECTION ######################################

x = subprocess.run(['curl', '-sS', '-L', '-H', "Accept: application/vnd.github+json", '-H', "Authorization: Bearer " + config_data.api_token, '-H', "X-GitHub-Api-Version: 2022-11-28", 'https://api.github.com/orgs/' + config_data.api_organization + '/settings/billing/actions'], stdout=subprocess.PIPE)

result=x.stdout.decode('UTF-8')
data=defaultdict(def_value)
data2=json.loads(result)
# It's possible the api query failed. If so, write info to log.
if "message" in data2:
    debuglog.write("API result message: " + str(data2["message"]) + "\n")
    debuglog.flush()
for k,v in data2.items():
    data[k]=v

print("gha_billing{owner=\"" + config_data.api_display_organization + "\", data_type=\"total_minutes_used\"} " + str(data["total_minutes_used"]))
print("gha_billing{owner=\"" + config_data.api_display_organization + "\", data_type=\"total_paid_minutes_used\"} " + str(data["total_paid_minutes_used"]))
print("gha_billing{owner=\"" + config_data.api_display_organization + "\", data_type=\"included_minutes\"} " + str(data["included_minutes"]))

# UPDATE SELF-HOSTED RUNNERS BASED ON THE BILLING DATA RESULTS ######################################

remaining_minutes=int(data["included_minutes"]) - int(data["total_minutes_used"])

lockfile=config_data.webroot + "/lockfile"
switchfile=config_data.webroot + "/switch"
if remaining_minutes<=int(config_data.minutes_buffer) and not(os.path.isfile(lockfile)):
    f = open(switchfile, "w")
    f.write("true")
    f.close()
    shutil.chown(switchfile, config_data.webuser, config_data.webgroup)
    debuglog.write("Set switch to true. Using self-hosted runners.")
elif remaining_minutes>0 and not(os.path.isfile(lockfile)):
    f = open(switchfile, "w")
    f.write("false")
    f.close()
    shutil.chown(switchfile, config_data.webuser, config_data.webgroup)
    debuglog.write("Set switch to false. Not using self-hosted runners.")
elif remaining_minutes>0 and os.path.isfile(lockfile):
    debuglog.write("Lockfile exists. Not modifying switch. It would have been set to false.")
elif remaining_minutes<=0 and os.path.isfile(lockfile):
    debuglog.write("Lockfile exists. Not modifying switch. It would have been set to true.")
elif os.path.isfile(lockfile):
    debuglog.write("Should not happen. Lockfile exists.")
else:
    debuglog.write("Should not happen.")

# Create a userinfo file

usageinfofile=config_data.webroot + "/usageinfo"
usagemessage="total_minutes_used: " + str(data["total_minutes_used"]) + "<br>total_paid_minutes_used: " + str(data["total_paid_minutes_used"]) + "<br>included_minutes: " + str(data["included_minutes"])
f = open(usageinfofile, "w")
f.write(usagemessage)
f.close()
shutil.chown(usageinfofile, config_data.webuser, config_data.webgroup)

# Completing

debuglog.close()
