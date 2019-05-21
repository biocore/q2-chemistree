# q2-qemistree
##### Canonically pronounced *chemis-tree*.

[![Build Status](https://travis-ci.org/biocore/q2-qemistree.svg?branch=master)](https://travis-ci.org/biocore/q2-qemistree) [![Coverage Status](https://coveralls.io/repos/github/biocore/q2-qemistree/badge.svg?branch=master)](https://coveralls.io/github/biocore/q2-qemistree?branch=master)

A tool to build a tree of MS1 features to compare chemical composition of samples in metabolomics experiments.

## Installation

Once QIIME 2 is [installed](https://docs.qiime2.org/2019.1/install/), activate your QIIME 2 environment and install q2-qemistree following the steps below:

```bash
git clone https://github.com/biocore/q2-qemistree.git
cd q2-qemistree
pip install .
qiime dev refresh-cache
```

q2-qemistree uses [SIRIUS](https://www.nature.com/articles/s41592-019-0344-8), a software-framework developed for de-novo identification of metabolites. We use molecular substrucures predicted by SIRIUS to build a hierarchy of the MS1 features in a dataset. For this demo, please download and unzip the latest version of SIRIUS from [here](https://bio.informatik.uni-jena.de/sirius/). Below, we download SIRIUS for macOS as follows (for linux the only thing that changes is the URL from which the binary is downloaded):

```bash
wget https://bio.informatik.uni-jena.de/repository/dist-release-local/de/unijena/bioinf/ms/sirius/4.0.1/sirius-4.0.1-osx64-headless.zip
unzip sirius-4.0.1-osx64-headless.zip
```

## Demonstration

`q2-qemistree` ships with the following methods:

```
qiime qemistree compute-fragmentation-trees
qiime qemistree rerank-molecular-formulas
qiime qemistree predict-fingerprints
qiime qemistree make-hierarchy
```

To generate a tree that relates the MS1 features in your experiment, we need to pre-process mass-spectrometry data (.mzXML files) using [MZmine2](http://mzmine.github.io) and produce the following inputs:

1. An MGF file with both MS1 and MS2 information. This file will be imported into QIIME 2 as a `MassSpectrometryFeatures` artifact.
2. A feature table with peak areas of MS1 ions per sample. This table will be imported from a CSV file into the [BIOM](http://biom-format.org/documentation/biom_conversion.html) format, and then into QIIME 2 as a `FeatureTable[Frequency]` artifact.

These input files can be obtained following peak detection in MZmine2. [Here](https://raw.githubusercontent.com/biocore/q2-qemistree/master/q2_qemistree/demo/batchQE-MZmine-2.33.xml) is an example MZmine2 batch file used to generate these.

To begin this demonstration, create a separate folder to store all the inputs and outputs:

```bash
mkdir demo-qemistree
cd demo-qemistree
```

Download a small feature table and MGF file using:

```bash
wget https://raw.githubusercontent.com/biocore/q2-qemistree/master/q2_qemistree/demo/feature-table.biom
wget https://raw.githubusercontent.com/biocore/q2-qemistree/master/q2_qemistree/demo/sirius.mgf
```

We [import](https://docs.qiime2.org/2018.11/tutorials/importing/) these files into the appropriate QIIME 2 artifact formats as follows:

```bash
qiime tools import --input-path feature-table.biom --output-path feature-table.qza --type FeatureTable[Frequency]
qiime tools import --input-path sirius.mgf --output-path sirius.mgf.qza --type MassSpectrometryFeatures
```

First, we generate [fragmentation trees](https://www.sciencedirect.com/science/article/pii/S0165993615000916) for molecular peaks detected using MZmine2:

```bash
qiime qemistree compute-fragmentation-trees --p-sirius-path 'sirius-osx64-4.0.1/bin' \
  --i-features sirius.mgf.qza \
  --p-ppm-max 15 \
  --p-profile orbitrap \
  --p-ionization-mode positive \
  --p-java-flags "-Djava.io.tmpdir=/path-to-some-dir/ -Xms16G -Xmx64G" \
  --o-fragmentation-trees fragmentation_trees.qza
```

This generates a QIIME 2 artifact of type `SiriusFolder`. This contains fragmentation trees with candidate molecular formulas for each MS1 feature detected in your experiment.
**Note**: `/path-to-some-dir/` should be a directory where you have write permissions and sufficient storage space. We use -Xms16G and -Xmx64G as the minimum and maximum heap size for Java virtual machine (JVM). If left blank, q2-qemistree will use default JVM flags.

Next, we select top scoring molecular formula as follows:

```bash
qiime qemistree rerank-molecular-formulas --p-sirius-path 'sirius-osx64-4.0.1/bin' \
  --i-features sirius.mgf.qza \
  --i-fragmentation-trees fragmentation_trees.qza \
  --p-zodiac-threshold 0.95 \
  --p-java-flags "-Djava.io.tmpdir=/path-to-some-dir/ -Xms16G -Xmx64G" \
  --o-molecular-formulas molecular_formulas.qza
```

This produces a QIIME 2 artifact of type `ZodiacFolder` with top-ranked molecular formula for MS1 features. Now, we predict molecular substructures in each feature based on the molecular formulas. We use [CSI:FingerID](https://www.pnas.org/content/112/41/12580) for this purpose as follows:

```bash
qiime qemistree predict-fingerprints --p-sirius-path 'sirius-osx64-4.0.1/bin' \
  --i-molecular-formulas molecular_formulas.qza \
  --p-ppm-max 20 \
  --p-java-flags "-Djava.io.tmpdir=/path-to-some-dir/ -Xms16G -Xmx64G" \
  --o-predicted-fingerprints fingerprints.qza
  ```

This gives us a QIIME 2 artifact of type `CSIFolder` that contains probabilities of molecular substructures (total 2936 molecular properties) within in each feature.
Now, we use these predicted molecular substructures to generate a hierarchy of molecules as follows:

```bash
qiime qemistree make-hierarchy \
  --i-csi-results fingerprints.qza \
  --i-feature-tables feature-table.qza \
  --o-tree demo-qemistree.qza \
  --o-merged-feature-table filtered-feature-table.qza
  --o-merged-feature-data feature-data.qza
```

To support meta-analyses, this method is capable of handling one or more datasets i.e pairs of CSI results and feature tables. Below is an example for two datasets:

```bash
qiime qemistree make-hierarchy \
  --i-csi-results fingerprints.qza \
  --i-csi-results fingerprints2.qza \
  --i-feature-tables feature-table.qza \
  --i-feature-tables feature-table2.qza
  --o-tree merged-qemistree.qza \
  --o-merged-feature-table merged-feature-table.qza \
  --o-merged-feature-data merged-feature-data.qza
```

**Note:** The input CSI results and feature tables should have a one-to-one correspondance i.e csi results and feature tables from all datasets should be provided in the same order.

This method generates the following:
1. A combined feature table by merging all the input feature tables; MS1 features without fingerprints are filtered out of this feature table. This is done because SIRIUS predicts molecular substructures for a subset of features (typically for 70-90% of all MS1 features) in an experiment (based on factors such as sample type, the quality MS2 spectra, and user-defined tolerances such as `--p-ppm-max`, `--p-zodiac-threshold`). This output is of type `FeatureTable[Frequency]`.
2. A tree relating the MS1 features in these data based on molecular substructures predicted for MS1 features. This is of type `Phylogeny[Rooted]`. By default, we only use PubChem fingerprints (total 489 molecular properties). Adding `--p-no-qc-properties` retains all (2936) the molecular properties in the contingency table.
**Note**: The latest release of [SIRIUS](https://www.nature.com/articles/s41592-019-0344-8) uses PubChem version downloaded on 13 August 2017.
3. A combined feature data file that contains unique identifiers of each feature, their corresponding original feature identifier, and feature tables that each feature was detected in. This is of type `FeatureData[Molecules]`. (The renaming of features needs to be done to avoid overlapping, non-unique feature identifiers in the original feature table)


Thus, using these steps, we can generate a tree relating MS1 features in a mass-spectrometry dataset along with a matched feature table. These can be used as inputs to perform chemical phylogeny-based [alpha-diversity](https://docs.qiime2.org/2019.1/plugins/available/diversity/alpha-phylogenetic/) and [beta-diversity](https://docs.qiime2.org/2019.1/plugins/available/diversity/beta-phylogenetic/) analyses.
