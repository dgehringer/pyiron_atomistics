import sys
from pyiron_base.objects.job.wrapper import JobWrapper

debug = False
job = JobWrapper(working_directory='/cmmc/u/mpt13/PyIron_data/website/pyiron_docs/source/example_notebooks/first_steps/Al_T400K_hdf5/Al_T400K',
                 job_id= 779503 ,
                 debug=False )
job.run()
