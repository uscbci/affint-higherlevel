#!/usr/bin/env python

import flywheel
import re
import json
import os,sys
from zipfile import ZipFile
from subprocess import call

#TASK
#In the future we can loop through a list of tasks
task="emoreg"
copes={"emoreg":[1,2,3,4,5,6,7,8,9,10]}

# Set directories in flywheel gear
FLYWHEEL_BASE = '/flywheel/v0'
OUTPUT_DIR='%s/output' % FLYWHEEL_BASE
INPUT_DIR='%s/input' % FLYWHEEL_BASE

# Grab Config
# CONFIG_FILE_PATH = '/flywheel/v0/config.json'
# with open(CONFIG_FILE_PATH) as config_file:
#     config = json.load(config_file)
# print(config)
# api_key = config['inputs']['api-key']['key']
# analysis_id = config['destination']['id']


##---------------------------------------
## VARIABLES TO ACTIVATE FOR LOCAL TESTING
##---------------------------------------

debug = 1

FLYWHEEL_BASE = '/Users/bciuser/fMRI/flywheel/affint/local_gear_testing'
OUTPUT_DIR='%s/output' % FLYWHEEL_BASE
INPUT_DIR='%s/input' % FLYWHEEL_BASE
COMMAND_LOCATION = '/Users/bciuser/fMRI/flywheel/affint/affint-higherlevel'
api_key = "uscdni.flywheel.io:oepWHsARl4CUfN6me6"
analysis_id = "5e58095e0c07dc25fd36bf72"

##---------------------------------------
## GET SUBJECT LIST AND LOWER-LEVEL DATA
##---------------------------------------

#Find the project this analysis is associated with
fw = flywheel.Client(api_key)
analysis = fw.get(analysis_id)  
parent  = analysis.parent

if parent.type != 'project':
	print('This gear must be run at the project level.')
	exit()
else:
	print('Project found.')
	projectid = parent.id
project = fw.get(projectid)
sessions = project.sessions()

#Find subjects associated with this project who have valid analyses
valid_subjects = []
input_feat_folders = []
for session in sessions:

	#Loop through subjects
	subject = session.subject.label
	print('Found subject: %s' % subject)

	#Find the lower-level feat analysis for this subject
	analyses = fw.get(session.id).analyses
	for analysis in analyses:
		if "affint-feat" in analysis.label:
			print(analysis.label)
			feat_analysis = analysis

	filename = "%s_%s.zip" % (subject,task)
	files = feat_analysis.files
	if files:
		featzip = [file for file in files if file.name == filename]
	else:
		print("Did not find affint-feat analysis file for subject %s" % subject)
		featzip = ""

	#Download the feat folder and unzip it
	if featzip:
		featzip = featzip[0]
		print("Downloading found file: %s" % featzip.name)
		dlfile = "%s/%s" % (INPUT_DIR,featzip.name)
		if not debug:
			featzip.download(dlfile)
		valid_subjects.append(subject)

		#lets unzip it
		output_folder = "%s/%s" % (INPUT_DIR,subject)
		print("unzipping...")
		if not debug:
			with ZipFile(dlfile,'r') as zipObj:
				zipObj.extractall(path=output_folder)
		input_feat_folders.append("%s/%s/flywheel/v0/output/%s_emoreg.feat" % (INPUT_DIR,subject,subject))

	else:
		print("Did not find affint-feat analysis file for subject %s" % subject)


print("Will include these subjects in the analysis: %s" % valid_subjects)
print("Will include these feats in the analysis: %s" % input_feat_folders)

##---------------------------------------
## CREATE A HIGHER LEVEL DESIGN FILE
##---------------------------------------

#Create file with inputfeats
inputfeats_filename = "%s/inputfeats.txt" % FLYWHEEL_BASE
featfile = open(inputfeats_filename,'w')
for feat in input_feat_folders:
	featfile.write(feat + "\n")
featfile.close()

#create higher level design
featoutputname = task + ".gfeat"
designfilename = "%s/%s.fsf" % (FLYWHEEL_BASE,task)
lowerlevelcopelist = " ".join([str(elem) for elem in copes[task]]) 

command = "%s/make_higherlevel_design.py --inputfeats %s --featoutputname %s --outputname %s --lowerlevelcopes %s" % (COMMAND_LOCATION,inputfeats_filename,featoutputname, designfilename,lowerlevelcopelist)
print(command)
call(command,shell=True)

##---------------------------------------
## RUN THE HIGHER LEVEL DESIGN
##---------------------------------------

#RUN FEAT
command = "feat %s" % designfilename
print(command)
call(command,shell=True)
