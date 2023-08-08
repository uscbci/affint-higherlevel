#!/usr/bin/env python

import os
from subprocess import call

folders = os.listdir("/Users/jonask/fMRI/flywheel/affint/affint-higherlevel/input")
folders = [elem for elem in folders if "zip" not in elem]

for folder in folders:
	subject = folder
	command = "fslstats /Users/jonask/fMRI/flywheel/affint/affint-higherlevel/input/%s/flywheel/v0/output/%s_emoreg.feat/reg_standard/mask -V" % (subject,subject)
	print(command)
	call(command,shell=True)