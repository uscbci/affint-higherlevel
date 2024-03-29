#!/opt/conda/bin/python
#
# Script to construct a higher level design.fsf file to run a feat analysis.
# We assume one group of subjects where EV1 models the mean and additional covariates are optional.
#
# Written by Jonas Kaplan jtkaplan@usc.edu
#

import argparse
from subprocess import call
import os
import re
import itertools

#command line options
parser = argparse.ArgumentParser()
parser.add_argument("--inputfeats",help="text file listing lower level feat directories, one on each line",action="store")
parser.add_argument("--featoutputname",help="name of .gfeat folder feat will create", action="store")
parser.add_argument("--regressors",help="additional higher-level one-column EV text files for covariates, a space separated list of files", nargs='+',action="store")
parser.add_argument("--lowerlevelcopes",help="which lower level copes to process, a space separated list of numbers", nargs="+",action="store")
parser.add_argument("--outputname",help="design file output name", action="store")
parser.add_argument("--task",help="task name", action="store")
args = parser.parse_args()

print("")
print("Creating higher level design for task %s" % args.task)


FLYWHEEL_BASE = '/flywheel/v0' # On Flywheel
template = "%s/template.fsf" % FLYWHEEL_BASE
standard = "%s/data/standard/MNI152_T1_2mm_brain" % os.environ['FSLDIR']

#-----------------------------
# read input feats file
#-----------------------------
featfile = open(args.inputfeats)
inputfeatfolders = featfile.readlines()
inputfeatfolders = [elem.strip() for elem in inputfeatfolders] 
numinputs = len(inputfeatfolders)
print("Found %d input feat folders" % numinputs)

#-----------------------------
#Check how many lower level copes there are
#-----------------------------
testdir = inputfeatfolders[0]
testcopes = os.listdir("%s/stats" % testdir)
numtotallowerlevels = len([elem for elem in testcopes if "varcope" in elem])

lowerlevelcopes = args.lowerlevelcopes
numcopes = len(lowerlevelcopes)
print("Found %d lower level copes" % numcopes)

#-----------------------------
#Check how many higher level EVs we have
#-----------------------------
if (args.regressors):
	numextraevs = len(args.regressors)
	regressors = args.regressors
	print("Will use these EV files as covariates: %s" % regressors)
else:
	numextraevs = 0
	regressors=[]
numevs = 1 + numextraevs
print("Found %d extra EVs for %d total including group mean" % (numextraevs,numevs))

#-----------------------------
#decide how many contrasts there will be
#-----------------------------

#mean plus positive and negative for each covariate
numcontrasts = 1 + 2*numextraevs
print("There will be %d total contrasts" % numcontrasts)

#-----------------------------
# Substitute in some basic variables
#-----------------------------

print("")
command = "sed -e 's/FEAT_OUTPUT_DIR/%s/g' -e 's/NUM_INPUTS/%s/g' -e 's/STANDARD_IMAGE/%s/g' -e 's/NUM_LOWER_LEVELS/%s/g' -e 's/NUMEVSORIG/%s/g' -e 's/NUMEVSREAL/%s/g' -e 's/NUMCONTRASTSORIG/%s/g' -e 's/NUMCONTRASTSREAL/%s/g' %s > %s" % (args.featoutputname.replace('/','\/'),numinputs,standard.replace('/','\/'),numtotallowerlevels,numevs,numevs,numcontrasts,numcontrasts,template,args.outputname)
#print(command)
call(command,shell=True)

#-----------------------------
# Add in copeinput section
#-----------------------------
#set fmri(copeinput.1) 1
copetext = ""
for x in range(1,numtotallowerlevels+1):
	if str(x) in lowerlevelcopes:
		value = 1
	else:
		value = 0
	text = "set fmri(copeinput.%s) %d" % (x,value)
	copetext = copetext + text + "\\\n"
command = "sed -ie 's/COPEINPUT/%s/g' %s" % (copetext,args.outputname)
#
#print(command)
call(command,shell=True)

#-----------------------------
# Add in input feat directories section
#-----------------------------
# 4D AVW data or FEAT directory (1)
feattext = ""
for x,feat in enumerate(inputfeatfolders):
	text = 'set feat_files(%d) "%s" ' % (x+1,feat.replace('/','\/')) 
	feattext = feattext + text + "\\\n"
command = "sed -ie 's/FEATFILES/%s/g' %s" % (feattext,args.outputname)
#print(command)
call(command,shell=True)


#-----------------------------
# Add in values for higher level EV1 in model (mean)
#-----------------------------
#set fmri(evg1.1) 1
evtext = ""
for x in range(1,numinputs+1):
	text = "set fmri(evg%d.1) 1" % (x)
	evtext = evtext + text + "\\\n"
command = "sed -ie 's/EV1VALUES/%s/g' %s" % (evtext,args.outputname)
#print(command)
call(command,shell=True)


if regressors:

	#-----------------------------
	# Add in EVs for regressors
	#-----------------------------

	orig_regressortext = """set fmri(evtitleEVNUM) \"EVTITLE\"
	set fmri(shapeEVNUM) 2
	set fmri(convolveshapeEVNUM) 0
	set fmri(convolve_phaseshapeEVNUM) 0
	set fmri(tempfilt_ynshapeEVNUM) 0
	set fmri(deriv_ynshapeEVNUM) 0
	set fmri(customshapeEVNUM) \"dummy\"
	"""

	evnum = 2
	regressortext = ""
	for regressor in regressors:
		
		#Determine regressor title from filename
		pattern = ".*%s_(.*)_evfile.txt" % args.task
		result = re.match(pattern,regressor)
		if result:
			regressortitle = result.groups()[0]
		else:
			print("Could not extract regressor title.")
		print("Regressor title: %s" % regressortitle)

		regressortextpart = orig_regressortext.replace("EVTITLE",regressortitle)
		regressortextpart = regressortextpart.replace("EVNUM",str(evnum))
		

		evfile = open(regressor)
		lines = evfile.readlines()
		evfile.close()
		lines = [elem.strip() for elem in lines]

		x=1
		for line in lines:
			text = "set fmri(evg%d.%d) %s" % (x,evnum,line)
			regressortextpart = regressortextpart + "\\n" + text
			x=x+1

		#EV options
		text = "set fmri(deriv_yn%d) 0" % evnum
		regressortextpart = regressortextpart +"\\n" + text

		text = "set fmri(tempfilt_yn%d) 0" % evnum
		regressortextpart = regressortextpart +"\\n" + text


		#CONTRASTS: Contrast numbers are 2 x (evnum-1)
		contrastnum = 2 * (evnum-1)
		text = "set fmri(conname_real.%d) \"%s+\"" % (contrastnum,regressortitle)
		regressortextpart = regressortextpart + "\\n" + text

		text = "set fmri(conpic_real.%d) 1" % contrastnum
		regressortextpart = regressortextpart +"\\n" + text

		for ev in range(1,numevs+1):
			if ev == evnum:
				contrastvalue = 1
			else:
				contrastvalue = 0
			text = "set fmri(con_real%d.%d) %d" % (contrastnum,ev,contrastvalue)
			regressortextpart = regressortextpart + "\\n" + text

		text = "set fmri(conname_real.%d) \"%s-\"" % (contrastnum+1,regressortitle)
		regressortextpart = regressortextpart + "\\n" + text

		text = "set fmri(conpic_real.%d) 1" % (contrastnum+1)
		regressortextpart = regressortextpart +"\\n" + text

		for ev in range(1,numevs+1):
			if ev == evnum:
				contrastvalue = -1
			else:
				contrastvalue = 0
			text = "set fmri(con_real%d.%d) %d" % (contrastnum+1,ev,contrastvalue)
			regressortextpart = regressortextpart + "\\n" + text

		#Describe orthogonalizations
		allevs = list(range(0,numevs+1))
		combos = list(itertools.product(allevs,allevs))
		for combo in combos:
			text = "set fmri(ortho%d.%d) 0" % (combo[0],combo[1])
			regressortextpart = regressortextpart + "\\n" + text

		#print(regressortext)
		evnum = evnum + 1
		regressortext = regressortext + "\n\n" + regressortextpart


	regressortext = regressortext.replace("\n","\\\n")
	command = "sed -ie 's/REGRESSORTEXT/%s/g' %s" % (regressortext,args.outputname)
	#print(command)
	call(command,shell=True)	

else:
	print("Cleaning up for no covariates")
	#We have to get rid of the regressor text
	command = "sed -ie 's/REGRESSORTEXT//g' %s" % (args.outputname)
	#print(command)
	call(command,shell=True)


#-----------------------------
# Add in group membership column in model
#-----------------------------
grouptext = ""
for x in range(1,numinputs+1):
	text = "set fmri(groupmem.%d) 1" % (x)
	grouptext = grouptext + text + "\\\n"
command = "sed -ie 's/EV1GROUPS/%s/g' %s" % (grouptext,args.outputname)
#print(command)
call(command,shell=True)