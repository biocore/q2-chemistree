#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Copyright (c) 2016-2018, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import warnings
import pandas as pd
import seaborn as sns
import click
import biom
from qiime2 import Artifact, Metadata


def classyfire_to_colors(classified_feature_data: pd.DataFrame,
                         classyfire_level: str, color_palette: str):
    '''This function generates a color map (dict) for unique Classyfire
    annotations in a user-specified Classyfire level.'''
    color_map = {}
    annotations = classified_feature_data[classyfire_level].unique()
    colors = sns.color_palette(color_palette,
                               n_colors=len(annotations)).as_hex()
    # give a heads up to the user
    if len(set(colors)) < len(annotations):
        warnings.warn("The mapping between colors and annotations"
                      " is not unique, some colors have been repeated",
                      UserWarning)
    for i, value in enumerate(annotations):
        color_map[value] = colors[i]
    return color_map


@click.command()
@click.option('--classified-feature-data', required=True, type=str,
              help='Path to feature data with Classyfire taxonomy.')
@click.option('--classyfire-level', default='class', type=str,
              help="One of the Classyfire levels in ['kingdom', "
              "'superclass', 'class', 'subclass', 'direct_parent']")
@click.option('--color-file-path', default='./itol_colors.txt', type=str,
              help='Path to file with colors specifications for tree clades')
@click.option('--label-file-path', default='./itol_labels.txt', type=str,
              help='Path to file with label specifications for tree tips')
@click.option('--color-palette', default='bright', type=str,
              help='Color palette for tree clades. One of the options'
              ' allowed by seaborn.color_palette()')
@click.option('--sample-feature-table', type=str,
              help='Path to sample feature table.')
@click.option('--sample-metadata', type=str,
              help='Path to sample metadata.')
@click.option('--sample-metadata-column', type=str,
              help='Categorical sample metadata column.')
@click.option('--barchart-file-path', default='./itol_bars.txt', type=str,
              help='Path to file with values for multi-value bar chart')
def get_itol_visualization(classified_feature_data: str,
                           classyfire_level: str = 'class',
                           color_file_path: str = './itol_colors.txt',
                           label_file_path: str = './itol_labels.txt',
                           color_palette: str = 'husl',
                           sample_feature_table: str = None,
                           sample_metadata: str = None,
                           sample_metadata_column: str = None,
                           barchart_file_path: str = './itol_bars.qza'):
    '''This function creates iTOL metadata files to specify clade colors and
    tip labels based on Classyfire annotations.'''
    fdata = Artifact.load(classified_feature_data).view(pd.DataFrame)
    color_map = classyfire_to_colors(fdata, classyfire_level, color_palette)
    with open(color_file_path, 'w+') as fh:
        fh.write('TREE_COLORS\n'
                 'SEPARATOR TAB\n'
                 'DATA\n')
        for idx in fdata.index:
            color = color_map[fdata.loc[idx, classyfire_level]]
            if fdata.loc[idx, 'annotation_type'] == 'MS2':
                fh.write(idx + '\t' + 'clade\t' +
                         color + '\tnormal\t6\n')
            if fdata.loc[idx, 'annotation_type'] == 'CSIFingerID':
                fh.write(idx + '\t' + 'clade\t' +
                         color + '\tdashed\t4\n')
    with open(label_file_path, 'w+') as fh:
        fh.write('LABELS\n'
                 'SEPARATOR TAB\n'
                 'DATA\n')
        for idx in fdata.index:
            label = fdata.loc[idx, classyfire_level]
            fh.write(idx + '\t' + label + '\n')

    # generate bar chart
    if barchart_file_path:
        get_itol_barchart(fdata, sample_feature_table, sample_metadata,
                          sample_metadata_column, barchart_file_path)


def get_itol_barchart(fdata: pd.DataFrame,
                      table_file: str,
                      metadata_file: str,
                      metadata_column: str,
                      output_file: str):
    '''Generate a table in QIIME 2 artifact format which can be directly
    parsed by iTOL and yield a multi-bar chart.
    '''
    # load sample feature table
    table = Artifact.load(table_file)

    # extract BIOM table
    table = table.view(biom.Table)

    # load sample metadata
    meta = Metadata.load(metadata_file)

    # generate a sample Id to category map
    column = meta.get_column(metadata_column).drop_missing_values()
    catmap = column.to_series().to_dict()

    # collapse feature table by category
    # note: when multiple samples map to one category, take **mean**
    table = table.collapse(lambda i, _: catmap[i], norm=True,
                           axis='sample')

    # import BIOM table into QIIME 2 and save
    res = Artifact.import_data('FeatureTable[Frequency]', table)
    res.save(output_file)


if __name__ == '__main__':
    get_itol_visualization()
