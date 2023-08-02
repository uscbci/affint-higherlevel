#!/opt/conda/bin/python

def make_evfile(regressor,subjects,task,outputdir,fw):

	print("Making EV file for regressor %s and task %s" % (regressor,task))
	
	success = 1

	included_subjects = []

	allvalues = []
	for subject in subjects:
		fullsubject = fw.get(subject.id)
		metadata = fullsubject.info
		if regressor in metadata:
			value = metadata[regressor]
			if (value):
				allvalues.append(value)
				included_subjects.append(subject)
				print ("%s for subject %s is %s" % (regressor,subject.label,value))
			else:
				print("%s for subject %s is empty" % (regressor,subject.label))
				success = 0
		else:
			print("Missing %s for subject %s" % (regressor,subject.label))
			success = 0


	print(allvalues)
	allvalues = [float(elem) for elem in allvalues]
	print("Original values: %s" % allvalues)
	mean = sum(allvalues)/len(allvalues)
	demeaned = [elem-mean for elem in allvalues]
	print("Demeaned values: %s" % demeaned)

	filename = "%s/%s_%s_evfile.txt" % (outputdir,task,regressor)
	evfile = open(filename, "w")
	for value in demeaned:
		evfile.write("%.3f\n" % value)
	evfile.close()

	return (included_subjects,filename)
