import pandas as pd

from magine.data.datatypes import ExperimentalData
from magine.data.formatter import pivot_tables_for_export
from magine.plotting.heatmaps import heatmap_from_array
from magine.plotting.species_plotting import plot_list_of_genes

data = pd.read_csv('Data/norris_et_al_2017_cisplatin_data.csv.gz',
                   low_memory=False)

exp_data = ExperimentalData(data)


# create a plotly interactive plot
plot_list_of_genes(data, ['BAX', 'BID'],
                     save_name='cisplatin_example',
                     out_dir='plots',
                     plot_type='plotly')

# create a matplotlib plot
plot_list_of_genes(data, ['BAX', 'BID'],
                     save_name='cisplatin_example',
                     out_dir='plots',
                     plot_type='matplotlib',
                     image_format='png')

# create a volcano plot

exp_data.time_series_volcano(exp_data_type='LF',
                             save_name='LF_volcano',
                             p_value=0.05,
                             fold_change_cutoff=1.5,
                             out_dir='plots',
                             )

# create clustered heatmap of significantly changed proteins only.
sig_data = exp_data.data[exp_data.data['significant_flag']]
prot, met = pivot_tables_for_export(sig_data)

heatmap_from_array(sig_data, cluster_row=False, convert_to_log=True,
                   index='protein', values='treated_control_fold_change',
                   columns='time_points', div_colors=True)