from .plugin_setup import plugin
from ._semantics import TSVMolecules
import pandas as pd
import qiime2


def _read_dataframe(fh):
    # Using `dtype=object` and `set_index` to avoid type casting/inference
    # of any columns or the index.
    df = pd.read_csv(fh, sep='\t', header=0, dtype='str')
    return df

# define a transformer from pd.DataFrame to -> TSVMolecules
@plugin.register_transformer
def _1(data: pd.DataFrame) -> TSVMolecules:
    ff = TSVMolecules()
    with ff.open() as fh:
        data.to_csv(fh, sep='\t', header=True)
    return ff

# define a transformer from TSVMolecules -> pd.DataFrame
@plugin.register_transformer
def _2(ff: TSVMolecules) -> pd.DataFrame:
    with ff.open() as fh:
        df = _read_dataframe(fh)
        # Using 'cluster index' as index explicity for library matches
        # since it may not be the first column
        if 'cluster index' in df.columns:
            df.set_index('cluster index', drop=True, append=False,
                         inplace=True)
        else:
            df.set_index(df.columns[0], drop=True, append=False, inplace=True)
        df.index.name = 'id'
        return df

# define a transformer from TSVMolecules -> qiime2.Metadata
# Based on the other transformers in this file, as well as the
# TaxonomyFormat -> qiime2.Metadata transformer in q2-types --
# https://github.com/qiime2/q2-types/blob/dc75cdeeb5e5535bc3c8bc703d06ef0adc1b58f9/q2_types/feature_data/_transformer.py#L170
@plugin.register_transformer
def _3(ff: TSVMolecules) -> qiime2.Metadata:
    with ff.open() as fh:
        df = _read_dataframe(fh)
        return qiime2.Metadata(df)
