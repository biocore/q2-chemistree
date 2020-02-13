# ----------------------------------------------------------------------------
# Copyright (c) 2016-2018, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from unittest import TestCase, main
import pandas as pd
import numpy as np
from skbio import TreeNode
from q2_qemistree import prune_hierarchy


class TestPruning(TestCase):
    def setUp(self):
        self.tree = TreeNode.read(["((A, B)C, D)root;"])
        self.big_tree = TreeNode.read(["((A, B)X, (C, D)Y)root;"])
        self.no_column = pd.DataFrame(index=['A', 'B', 'D'],
                                      data=[np.nan, np.nan, np.nan])
        self.no_annotation = pd.DataFrame(index=['A', 'B', 'D'],
                                          data=['unclassified', 'unclassified',
                                                'unclassified'],
                                          columns=['class'])
        self.index_filter = pd.DataFrame(index=['A', 'B', 'D'],
                                         data=[['foo', ':)'],
                                               ['unclassified', ':)'],
                                               ['unclassified', ':D']],
                                         columns=['class', 'faces'])
        self.no_overlap = pd.DataFrame(index=['X', 'Y', 'Z'],
                                       data=['foo', 'bar', 'unclassified'],
                                       columns=['class'])
        self.one_overlap = pd.DataFrame(index=['A', 'Y', 'Z'],
                                        data=['foo', 'bar', 'unclassified'],
                                        columns=['class'])
        self.feature_data = pd.DataFrame(index=['A', 'B', 'C', 'D'],
                                         data=[['foo', ':)'],
                                               ['bleep', ':)'],
                                               ['unclassified', ':D'],
                                               ['bar', ':D']],
                                         columns=['class', 'faces'])

    def test_no_smiles(self):
        msg = "The feature data does not contain the column 'csi_smiles'"
        with self.assertRaisesRegex(ValueError, msg):
            prune_hierarchy(self.no_column, self.tree, 'csi_smiles')

    def test_no_annotation(self):
        msg = ('Tree pruning aborted! There are less than two tree '
               'tips after pruning. Please check if the correct '
               'feature data table was provided.')
        with self.assertRaisesRegex(ValueError, msg):
            prune_hierarchy(self.no_annotation, self.tree, 'class')

    def test_index_filter(self):
        tree = prune_hierarchy(self.index_filter, self.tree)
        self.assertEqual({t.name for t in tree.tips()}, {'A', 'B', 'D'})

    def test_no_overlap(self):
        msg = ('Tree pruning aborted! There are less than two tree '
               'tips after pruning. Please check if the correct '
               'feature data table was provided.')
        with self.assertRaisesRegex(ValueError, msg):
            prune_hierarchy(self.no_overlap, self.tree, 'class')

    def test_one_overlap(self):
        msg = ('Tree pruning aborted! There are less than two tree '
               'tips after pruning. Please check if the correct '
               'feature data table was provided.')
        with self.assertRaisesRegex(ValueError, msg):
            prune_hierarchy(self.one_overlap, self.tree, 'class')

    def test_filtering(self):
        tree = prune_hierarchy(self.feature_data, self.tree, 'class')
        self.assertEqual({t.name for t in tree.tips()}, {'A', 'B', 'D'})

    def test_filtering_complete(self):
        self.feature_data.loc['C', 'class'] = 'baz'
        tree = prune_hierarchy(self.feature_data, self.big_tree, 'class')
        self.assertEqual({t.name for t in tree.tips()}, {'A', 'B', 'C', 'D'})


if __name__ == '__main__':
    main()
