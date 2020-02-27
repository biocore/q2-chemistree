# ----------------------------------------------------------------------------
# Copyright (c) 2016-2018, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import requests
import pandas as pd
import numpy as np
import warnings
import urllib


def get_classyfire_taxonomy(feature_data: pd.DataFrame) -> pd.DataFrame:
    '''This function uses structural predictions of molecules (SMILES)
    to run Classyfire and obtain chemical taxonomy for each mass-spec feature.
    It appends chemical taxonomy of features to feature data table.

    Parameters
    ----------
    feature_data : pd.DataFrame
        a table that maps MD5 hash of mass-spec features to their structural
        annotations (SMILES)

    Raises
    ------
    ValueError
        If feature data does not contain the column 'csi_smiles' and
        'ms2_smiles'
        If all SMILES are NaNs

    Returns
    -------
    pd.DataFrame
        feature data table with Classyfire annotations ('kingdom',
        'superclass', 'class','subclass', 'direct_parent') per mass-spec
        feature
    '''
    classyfire_levels = ['kingdom', 'superclass', 'class', 'subclass',
                         'direct_parent']
    smiles = {'csi_smiles', 'ms2_smiles'}
    if not smiles.issubset(feature_data.columns):
        raise ValueError('Feature data table must contain the columns '
                         '`csi_smiles` and `ms2_smiles` '
                         'to run Classyfire')
    for idx in feature_data.index:
        ms2_smiles = feature_data.loc[idx, 'ms2_smiles']
        csi_smiles = feature_data.loc[idx, 'csi_smiles']
        if ms2_smiles != 'missing':
            feature_data.loc[idx, 'smiles'] = ms2_smiles
            feature_data.loc[idx, 'structure_source'] = 'MS2'
        elif csi_smiles != 'missing':
            feature_data.loc[idx, 'smiles'] = csi_smiles
            feature_data.loc[idx, 'structure_source'] = 'CSIFingerID'
        else:
            feature_data.loc[idx, 'smiles'] = np.nan
            feature_data.loc[idx, 'structure_source'] = np.nan
    if feature_data['smiles'].notna().sum() == 0:
        raise ValueError("The feature data table should have at least "
                         "one structural annotation to run Classyfire")
    feature_data = feature_data.fillna('missing')

    classyfire = {}
    no_inchikey = []
    unexpected = []
    for idx in feature_data.index:
        smiles = feature_data.loc[idx, 'smiles']
        if smiles != 'missing':
            to_inchikey = 'https://gnps-structure.ucsd.edu/inchikey?smiles='
            urlencoded_smiles = urllib.parse.quote(smiles)
            response = requests.get(to_inchikey+urlencoded_smiles)
            if response.status_code != 200:
                classyfire[idx] = 'SMILE parse error'
                no_inchikey.append((idx, smiles))
                continue
            inchikey = response.text
            to_classyfire = 'https://gnps-classyfire.ucsd.edu/entities/'
            response = requests.get(to_classyfire+str(inchikey)+'.json')
            if response.status_code == 200:
                response = response.json()
                sublevels = [level for level in classyfire_levels
                             if level in response]
                if len(sublevels) == 0:
                    classyfire[idx] = 'unclassified'
                    continue
                taxonomy = []
                for level in classyfire_levels:
                    if (response and level in sublevels and
                            response[level] is not None):
                        taxonomy.append(response[level]['name'])
                    else:
                        taxonomy.append('unclassified')
                classyfire[idx] = taxonomy
            elif response.status_code == 404:
                classyfire[idx] = 'unclassified'
            else:
                classyfire[idx] = 'unexpected server response'
                unexpected.append((idx, smiles, response.status_code))
        else:
            classyfire[idx] = 'unclassified'
    if bool(no_inchikey):
        warnings.warn('The following structures (id, SMILES) could not be used'
                      ' to retrieve an InChIKey from Classyfire:\n' +
                      ', '.join(str(i) for i in no_inchikey), UserWarning)
    if bool(unexpected):
        warnings.warn('The following features produced unexpected '
                      'server response codes (id, SMILES, response code):\n'
                      ', '.join(str(i) for i in unexpected) + '\n'
                      'More information about response status codes can be '
                      'found here:\n' +
                      'https://www.ietf.org/assignments/http-status-codes/'
                      'http-status-codes.txt', UserWarning)
    classyfire = pd.DataFrame(classyfire, index=classyfire_levels).T
    classified_feature_data = pd.concat([feature_data, classyfire],
                                        sort=False, axis=1)
    return classified_feature_data
