import gzip
import itertools
import os

import pandas as pd
from bioservices import UniChem
from sortedcontainers import SortedSet, SortedDict

from magine.data.storage import id_mapping_dir

try:
    import cPickle as pickle
except:  # python3 doesnt have cPickle
    import pickle
try:
    basestring
# Allows isinstance(foo, basestring) to work in Python 3
except:
    basestring = str

chem = UniChem()


class ChemicalMapper(object):
    """
    converts chemical species ids
    Database was creating using HMDB


    Attributes
    ----------
    hmdb_to_chem_name : dict
    chem_name_to_hmdb : dict
    hmdb_to_kegg : dict
    kegg_to_hmdb : dict
    hmdb_to_protein : dict
    synonyms_to_hmdb : dict

    """

    valid_columns = ['kegg_id', 'name', 'accession', 'chebi_id', 'inchikey',
                     'chemspider_id', 'biocyc_id', 'synonyms', 'iupac_name',
                     'pubchem_compound_id', 'protein_associations',
                     'ontology', 'drugbank_id', 'chemical_formula',
                     'smiles', 'metlin_id', 'average_molecular_weight',
                     'secondary_accessions'
                     ]

    def __init__(self):

        self.database = None
        self.hmdb_to_chem_name = dict()
        self.chem_name_to_hmdb = dict()
        self.hmdb_to_kegg = dict()
        self.kegg_to_hmdb = dict()
        self.synonyms_to_hmdb = dict()
        self.drugbank_to_hmdb = dict()
        self.hmdb_to_protein = dict()
        self.hmdb_main_to_protein = dict()

        self._instance_filename = os.path.join(id_mapping_dir,
                                               'hmdb_instance.p.gz')

        try:
            self.reload()
            print('Loading class data')
        except:
            print('Initializing Chemical mapping')
            self.load()

    def load(self):

        _filename = os.path.join(id_mapping_dir, 'hmdb_dataframe.csv.gz')

        if not os.path.exists(_filename):
            from magine.mappings.databases.download_libraries import HMDB
            HMDB()
        hmdb_database = pd.read_csv(
            _filename, low_memory=False, encoding='utf-8',
            converters={
                "protein_associations": lambda x: x.split("|"),
                "cellular_locations": lambda x: x.split("|"),
                "biofunction": lambda x: x.split("|"),
                "synonyms": lambda x: x.split("|"),
                # "secondary_accessions": lambda x: x.split("|"),
            }
        )
        self.database = hmdb_database.where((pd.notnull(hmdb_database)), None)

        self.database['main_accession'] = self.database['accession']
        sub_db = self.database[
            self.database['secondary_accessions'].str.contains('|', na=False)]
        new_df = tidy_split(sub_db, 'secondary_accessions', '|')
        new_df['accession'] = new_df['secondary_accessions']
        self.database = pd.concat([self.database, new_df])

        self.hmdb_to_chem_name = self._to_dict("accession", "name")
        self.chem_name_to_hmdb = self._to_dict("name", "main_accession")
        self.hmdb_to_kegg = self._to_dict("accession", "kegg_id")

        self.kegg_to_hmdb = self._to_dict("kegg_id", "main_accession")
        self.hmdb_to_protein = self._from_list_dict("accession",
                                                    "protein_associations")

        self.hmdb_main_to_protein = self._from_list_dict(
            "main_accession", "protein_associations")

        self.drugbank_to_hmdb = self._to_dict('drugbank_id', 'main_accession')
        self.synonyms_to_hmdb = None

        self.save()

    def _to_dict(self, key, value):
        """ creates a dictionary with a list of values for each key

        Parameters
        ----------
        key : str
        value : str

        Returns
        -------
        dict

        """
        d = self.database[[key, value]].copy()
        d.dropna(how='any', inplace=True)
        return_dict = SortedDict()
        for i, j in d.values:
            if i in return_dict:
                return_dict[i].add(j)
            else:
                return_dict[i] = SortedSet([j])
        return return_dict

    def _from_list_dict(self, key, value):
        return {k: sorted(set(list(itertools.chain.from_iterable(v.tolist()))))
                for k, v in self.database.groupby(key)[value]}

    def convert_to_dict_from_list(self, key, value):
        """ creates a dictionary from hmdb with a list of values for each key

        Parameters
        ----------
        key : str
        value : str

        Returns
        -------
        dict

        """

        tmp_dict = {}
        for k, v in self.database.groupby(key)[value]:
            v = v.tolist()[0]
            if isinstance(v, list):
                if len(v) > 0:
                    if v[0] is not None:
                        tmp_dict[k] = v

        return tmp_dict

    def check_synonym_dict(self, term, format_name):
        """ checks hmdb database for synonyms and returns formatted name

        Parameters
        ----------
        term : str
        format_name : str

        Returns
        -------
        dict


        Examples
        --------
        >>> cm = ChemicalMapper()
        >>> cm.check_synonym_dict(term='dodecene', format_name='main_accession')
        ['HMDB0000933', 'HMDB0059874']

        """
        synonyms = self.database[['synonyms', format_name]].copy()
        synonyms['synonyms'] = synonyms['synonyms'].apply(','.join)
        synonyms['synonyms'] = synonyms['synonyms'].str.lower()

        hits = synonyms[synonyms['synonyms'].str.contains(term.lower())]
        matches = sorted(set(hits[format_name].values))
        return matches

    def print_info(self):
        """ print information about the dataframe

        Returns
        -------

        """
        print('Number of HMDB accessions = {0}'.format(
            len(self.database['accession'].unique())))
        print('Number of unique KEGG ids = {0}'.format(
            len(self.hmdb_to_kegg.keys())))
        print('Number of HMDB to KEGG mappings = {0}'.format(
            len(self.kegg_to_hmdb.values())))

    def save(self):
        """ save class instance

        Returns
        -------

        """
        print('Saving class data')
        with gzip.open(self._instance_filename, 'wb') as f:
            f.write(pickle.dumps(self.__dict__, protocol=0))

    def reload(self):
        """ loads class instance

        Returns
        -------

        """
        try:
            with gzip.open(self._instance_filename, 'rb') as f:
                data = f.read()
            self.__dict__ = pickle.loads(data)
        except:
            with gzip.open(self._instance_filename, 'rb') as f:
                data = f.read()
            self.__dict__ = pickle.loads(data, encoding='latin1')

    def convert_kegg_nodes(self, network):
        """
        Maps network from kegg to gene names

        Parameters
        ----------
        network : networkx.DiGraph

        Returns
        -------
        dict

        """
        cpd_to_hmdb = {}  # he
        still_unknown = []
        nodes = set(network.nodes())

        hits = [i for i in nodes if i.startswith('cpd:')]

        for i in hits:

            name_stripped = i.lstrip('cpd:')
            network.node[i]['keggName'] = name_stripped

            if name_stripped in self.kegg_to_hmdb:
                mapping = self.kegg_to_hmdb[name_stripped]
                if isinstance(mapping, (list, SortedSet)):
                    names = '|'.join(set(mapping))
                    cpd_to_hmdb[i] = names
                    network.node[i]['hmdbNames'] = names
                    chem_names = set()
                    for name in mapping:
                        if name in self.hmdb_to_chem_name:
                            chem_names.update(
                                set(self.hmdb_to_chem_name[name]))
                    network.node[i]['chemName'] = '|'.join(chem_names)

                elif isinstance(mapping, basestring):
                    cpd_to_hmdb[i] = mapping
                    chem_n = self.hmdb_to_chem_name[mapping]
                    network.node[i]['chemName'] = chem_n.encode('ascii',
                                                                'ignore')
                else:
                    print('Returned something else...', mapping)

            elif i in compound_manual:
                loc = compound_manual[i]
                if loc in self.hmdb_to_chem_name:
                    chem_names = '|'.join(set(self.hmdb_to_chem_name[loc]))
                    network.node[i]['chemName'] = chem_names
                    continue
                else:
                    if i in common_names_not_in_hmdb:
                        network.node[i]['chemName'] = common_names_not_in_hmdb[
                            i]
                    else:
                        print("Need to add common name for {}".format(i))
                        network.node[i]['chemName'] = name_stripped
            else:
                still_unknown.append(i)
        if len(still_unknown) == 0:
            return cpd_to_hmdb
        kegg_hmdb = chem.get_mapping("kegg_ligand", "hmdb")
        for i in still_unknown:
            if i.lstrip('cpd') in kegg_hmdb:
                cpd_to_hmdb[i] = kegg_hmdb[i.lstrip('cpd:')][0]
            # else:
            #     print("Cannot find a HMDB mapping for %s " % i)
        return cpd_to_hmdb


compound_manual = {'cpd:C07909': 'HMDB15015',
                   'cpd:C16844': 'HMDB01039',
                   'cpd:C00076': 'HMDB00464',
                   'cpd:C00154': 'HMDB01338',
                   'cpd:C01561': 'HMDB03550',
                   'cpd:C04043': 'HMDB03791',
                   'cpd:C01165': 'HMDB02104',
                   'cpd:C00025': 'HMDB00148',
                   'cpd:C00696': 'HMDB01403',
                   'cpd:C00124': 'HMDB00143',
                   }
common_names_not_in_hmdb = {'cpd:C00124': 'D-Galactose'}


def tidy_split(df, column, sep='|', keep=False):
    """
    Split the values of a column and expand so the new DataFrame has one split
    value per row. Filters rows where the column is missing.

    Params
    ------
    df : pandas.DataFrame
        dataframe with the column to split and expand
    column : str
        the column to split and expand
    sep : str
        the string used to split the column's values
    keep : bool
        whether to retain the presplit value as it's own row

    Returns
    -------
    pandas.DataFrame
        Returns a dataframe with the same columns as `df`.
    """
    indexes = list()
    new_values = list()
    df = df.dropna(subset=[column])
    for i, presplit in enumerate(df[column].astype(str)):
        values = presplit.split(sep)
        if keep and len(values) > 1:
            indexes.append(i)
            new_values.append(presplit)
        for value in values:
            indexes.append(i)
            new_values.append(value)
    new_df = df.iloc[indexes, :].copy()
    new_df[column] = new_values
    return new_df


if __name__ == "__main__":
    cm = ChemicalMapper()
    cm.load()
    cm._to_dict('drugbank_id', 'main_accession')
    # print(list(cm.hmdb_to_protein)[:10])
    # print(cm.hmdb_to_protein['HMDB00005'])
    print(cm.check_synonym_dict(term='dodecene', format_name='main_accession'))
