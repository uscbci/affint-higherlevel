#!/usr/bin/env python
#
# Script to construct a higher level design.fsf file to run a feat analysis.
# We assume one group of subjects where EV1 models the mean and additional covariates are optional.
#
# Written by Jonas Kaplan jtkaplan@usc.edu
#

import argparse
from subprocess import call
import os

#command line options
parser = argparse.ArgumentParser()
parser.add_argument("--inputfeats",help="text file listing lower level feat directories, one on each line",action="store")
parser.add_argument("--featoutputname",help="name of .gfeat folder feat will create", action="store")
parser.add_argument("--regressors",help="additional higher-level one-column EV text files for covariates, a space separated list of files", nargs='+',action="store")
parser.add_argument("--lowerlevelcopes",help="which lower level copes to process, a space separated list of numbers", nargs="+",action="store")
parser.add_argument("--outputname",help="design file output name", action="store")
args = parser.parse_args()

print()

FLYWHEEL_BASE = '/flywheel/v0' # On Flywheel
#FLYWHEEL_BASE = '/Users/bciuser/fMRI/flywheel/affint/local_gear_testing/input' #Local testing
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
else:
	numextraevs = 0
numevs = 1 + numextraevs
print("Found %d extra EVs for %d total including group mean" % (numextraevs,numevs))

#-----------------------------
#decide how many contrasts there will be
#-----------------------------

#mean plus positive and negative for each covariate
numcontrasts = 1 + 2*numextraevs


#-----------------------------
# Substitute in some basic variables
#-----------------------------

print()
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