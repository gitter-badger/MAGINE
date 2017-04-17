import os

from magine.data.datatypes import ExperimentalData

data_dir = os.path.dirname(__file__)
exp_data = ExperimentalData(proteomics_file='large_example.csv',
                            data_directory=os.path.join(data_dir, 'Data'))