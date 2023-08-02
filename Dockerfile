# Create a base docker container that will run FSL's FEAT
#
#

FROM uscbci/fmri:1.8

MAINTAINER Jonas Kaplan <jtkaplan@usc.edu>

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY run.sh ${FLYWHEEL}/run.sh
COPY template.fsf ${FLYWHEEL}/

# Configure entrypoint
# ENTRYPOINT ["/flywheel/v0/run.py"]
