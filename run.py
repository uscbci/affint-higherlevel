#!/opt/conda/bin/python

import flywheel
import re
import json
import os,sys
from zipfile import ZipFile
from subprocess import call
import shutil
from make_evfile import make_evfile
from packaging import version

# Set directories in flywheel gear
FLYWHEEL_BASE = '/flywheel/v0'
OUTPUT_DIR='%s/output' % FLYWHEEL_BASE
INPUT_DIR='%s/input' % FLYWHEEL_BASE
COMMAND_LOCATION = FLYWHEEL_BASE

if not os.path.exists(INPUT_DIR):
		os.mkdir(INPUT_DIR)

# Grab Config
CONFIG_FILE_PATH = '/flywheel/v0/config.json'
with open(CONFIG_FILE_PATH) as config_file:
    config = json.load(config_file)
api_key = config['inputs']['api-key']['key']
analysis_id = config['destination']['id']

subjectinput = config['config']['subjects']
regressors = config['config']['covariates']
exclude = config['config']['exclude']
tasks = config['config']['task']

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), 
                       os.path.relpath(os.path.join(root, file), 
                                       os.path.join(path, '..')))

##---------------------------------------
## VARIABLES TO ACTIVATE FOR LOCAL TESTING
##---------------------------------------

download_files = 1 	#Can turn this off if we have the files already
debug = 1		 	#Will print out debugging info

if debug:
	print("Debugging mode is ON")
	print(config)
	base = os.listdir(FLYWHEEL_BASE)
	print(base)

#tasks = ["faceemotion","emoreg","tom"]
# emoreg: 10 contrasts
# tom: 12 contrasts
# faces: 5 contrasts

copes={"emoreg":[1,2,3,4,5,6,7,8,9,10],"tom":[1,2,3,4,5,6,7,8,9,10,11,12],"faceemotion":[1,2,3,4,5]}

subjectstoinclude = subjectinput.split()
regressors = regressors.split()
tasks = tasks.split()

if regressors[0]=="none":
	regressors=[]

##---------------------------------------
## CONNECT TO FLYWHEEL AND GET PROJECT INFO
##---------------------------------------
fw = flywheel.Client(api_key)
# analysis = fw.get(analysis_id)  
# parent  = analysis.parent
# if parent.type != 'project':
# 	print('This gear must be run at the project level.')
# 	exit()
# else:
# 	print('Project found.')
# 	projectid = parent.id
projectid = '5d30b3665437ef00342d791e'
project = fw.get(projectid)
sessions = project.sessions()

evfilelist = []

for task in tasks:

	##---------------------------------------
	## GET SUBJECT LIST AND LOWER-LEVEL DATA
	##---------------------------------------

	print('Starting task %s' % task)
	#Find subjects associated with this project who have valid analyses
	valid_subjects = []
	valid_subject_containers = []
	input_feat_folders = []
	for sess in sessions:

		session = fw.get_session(sess.id)
		#Looping through subjects
		subject = session.subject.label
		print("Retrieved session for subject %s" % subject)
		if subjectstoinclude[0]=="all" or subject in subjectstoinclude:
			if subject not in exclude:
				subject_container = session.subject
				print('Found subject: %s' % subject)

				#Find the lower-level feat analysis for this subject
				analyses = session.analyses
				for analysis in analyses:
					if analysis.gear_info.name == "affint-feat":
						if version.parse(analysis.gear_info.version) > version.parse("0.3.15"):
							print(analysis.label)
							feat_analysis = analysis

				filename = "%s_%s.zip" % (subject,task)
				files = feat_analysis.files
				if files:
					featzip = [file for file in files if file.name == filename]
				else:
					print("Did not find zipfile for task %s in affint-feat analysis file for subject %s" % (task,subject))
					featzip = ""

				#Download the feat folder and unzip it
				if featzip:
					featzip = featzip[0]
					print("Downloading found file: %s" % featzip.name)
					dlfile = "%s/%s" % (INPUT_DIR,featzip.name)
					if download_files:
						featzip.download(dlfile)
					valid_subjects.append(subject)
					valid_subject_containers.append(subject_container)

					#lets unzip it
					output_folder = "%s/%s" % (INPUT_DIR,subject)
					print("unzipping to... %s" % output_folder)
					if download_files:
						with ZipFile(dlfile,'r') as zipObj:
							zipObj.extractall(path=output_folder)
					input_feat_folders.append("%s/%s/flywheel/v0/output/%s_%s.feat" % (INPUT_DIR,subject,subject,task))


	#Make the EV files for this task
	evfilelist=[]
	if (len(regressors) > 0):
		for regressor in regressors:
				(final_subject_list,evfilename) = make_evfile(regressor,valid_subject_containers,task,OUTPUT_DIR,fw)
				if evfilename=="error":
					print("Will not include regressor due to missing data.")
				else:
					evfilelist.append(evfilename)
	else:
		final_subject_list = valid_subjects
	
	print("Final subject list:")
	print(final_subject_list)

	final_input_feat_folders = []
	for folder in input_feat_folders:
		print("Checking if folder %s should be in final list..." % folder)
		pattern = ".*(AI\d+)_.*"
		thissubject = re.match(pattern,folder).groups()[0]
		if thissubject in final_subject_list:
			final_input_feat_folders.append(folder)

	print("Will include these subjects in the analysis: %s" % final_subject_list)


	print("Will include these feats in the analysis: %s" % final_input_feat_folders)
	print("----------------------------------------------------")

	##---------------------------------------
	## CREATE A HIGHER LEVEL DESIGN FILE
	##---------------------------------------

	#Create file with inputfeats

	inputfeats_filename = "%s/inputfeats.txt" % FLYWHEEL_BASE
	if os.path.exists(inputfeats_filename):
		os.remove(inputfeats_filename)

	featfile = open(inputfeats_filename,'w')
	for feat in final_input_feat_folders:
		featfile.write(feat + "\n")
	featfile.close()

	#create higher level design
	featoutputname = "%s/%s.gfeat" % (OUTPUT_DIR,task)
	designfilename = "%s/%s.fsf" % (FLYWHEEL_BASE,task)
	lowerlevelcopelist = " ".join([str(elem) for elem in copes[task]]) 
	evfilestring = " ".join(evfilelist) 

	command = "%s/make_higherlevel_design.py --inputfeats %s --featoutputname %s --outputname %s --lowerlevelcopes %s --task %s" % (COMMAND_LOCATION,inputfeats_filename,featoutputname, designfilename,lowerlevelcopelist,task)
	
	if regressors:
		command = "%s --regressors %s" % (command,evfilestring)

	print(command)
	call(command,shell=True)

	print("AFTER make_higherlevel-----------------------------------------------------------")

	##---------------------------------------
	## RUN THE HIGHER LEVEL DESIGN
	##---------------------------------------

	#MOVE A COPY TO THE OUTPUT FOLDER SO WE HAVE IT
	command = "cp %s %s/%s.fsf" % (designfilename,OUTPUT_DIR,task)
	print(command)
	call(command,shell=True)

	#RUN FEAT
	#We will source the FSL config script before invoking feat
	print("Starting feat analysis...")
	command = "export USER=Flywheel; . $FSLDIR/etc/fslconf/fsl.sh; time feat %s" % designfilename
	print(command)
	call(command,shell=True)


	##---------------------------------------
	## PACKAGE THE OUTPUT
	##---------------------------------------

	for cope in copes[task]:
		input_html_file = "%s/cope%d.feat/report_poststats.html" % (featoutputname,cope)
		output_html_file = "%s/%s_report_poststats_cope%d.html" % (OUTPUT_DIR,task,cope)

		print("Preparing %s to %s" % (input_html_file,output_html_file))

		command = 'python /opt/webpage2html/webpage2html.py -q -s %s > "%s"' % (input_html_file,output_html_file)
		print(command)
		call(command,shell=True)

	print("\nZipping feat directory....")
	output_filename = "%s/%s.zip" % (OUTPUT_DIR,task)
	#shutil.make_archive(output_filename, 'zip', featoutputname)

	zf = ZipFile(output_filename, mode='w', allowZip64 = True)
	zipdir(featoutputname,zf)
	zf.close()

	print("\nCleaning up...")
	shutil.rmtree(featoutputname, ignore_errors=True)