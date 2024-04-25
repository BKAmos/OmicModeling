## Notes
# Definitions
# CIRI2_#junction_reads = ciri2 read counts
# CLEAR_readNumber = clear read counts

## Things to do with this data
# 1 filter to runs where only deep or shallow sequencing reads are compared - no need to TPM normalize if there is no combing across data
# 2 remove reads at 1 or below
# 3 analyze data from CIRI2 or CLEAR in isolation in either deep or shallow sequencing
# 4 seperate data by round and compare as there seems to be high correlation amongts genes from certain rounds

#%% Read in your libraries
import pandas as pd
import numpy as np
import seaborn as sns
import PyWGCNA
import pickle
import seaborn as sns
import matplotlib.pyplot as plt

#%% Read in your files circRNA Files
lotusCircRNA = pd.read_csv('data.csv', index_col=False)


#%% Create a unique column for futher processing as well as replace the comma seperating id names witha  semicolon
lotusCircRNA['Unique'] = lotusCircRNA['Sample_number'].astype(str) + '_' + lotusCircRNA['Depth']
lotusCircRNA['New_ID'] = lotusCircRNA['New_ID'].str.replace(',', ';')


#%% This line of code is for summing reads across dataframes for a non-normalized read count table
lotusCircRNA['Total_Count'] = lotusCircRNA['CLEAR_readNumber'].add(lotusCircRNA['CIRI2_#junction_reads'], fill_value=0)


#%% The below code applies tpm normalization across two different circRNA data production files read counts. This results in a column devoid of NA and containing TPM information. Works for the symbiosis data
# lotusCircRNA['CIRI2_RPK'] = (lotusCircRNA['CIRI2_#junction_reads']/(lotusCircRNA['circ_len']/1000)) 
# lotusCircRNA['CLEAR_RPK'] = (lotusCircRNA['CLEAR_readNumber']/(lotusCircRNA['circ_len']/1000)) 
# lotusCircRNA['RPK'] = lotusCircRNA['CLEAR_RPK'].add(lotusCircRNA['CIRI2_RPK'], fill_value=0) 
# lotusCircRNA['RPK_Sum_Sample'] = lotusCircRNA.groupby('Sample_number')['RPK'].transform('count')
# lotusCircRNA['perMillScale'] = lotusCircRNA['RPK_Sum_Sample']/1000000
# lotusCircRNA['TPM'] = lotusCircRNA['RPK']/lotusCircRNA['perMillScale']


#%% Create a Clear Dataframe with only roud D data
# lotusCircRNA = lotusCircRNA.loc[lotusCircRNA['Round'] == 'a']


#%% Create deep pivot table based on isolated data from Ciri and Clear data
lotusCircDeep = pd.pivot_table(lotusCircRNA, values = 'Total_Count', index = 'Unique', columns='New_ID', aggfunc='sum', fill_value=0)
lotusCircDeep.rename(columns=lambda x: x.replace(',', ';'), inplace=True)


#%% Drop reads for genes based on mean read count for the frame
# all data = 1
# all data round d = 1
# all data round c = 4
# all data round b = 3
# all data round a = 1
column_sums = lotusCircDeep.sum()
columns_to_drop =  column_sums[column_sums <= 1].index
lotusCircDeep = lotusCircDeep.drop(columns=columns_to_drop)


#%% create Sample Meta for symbiosis Experiment
sample_meta = lotusCircRNA[['Unique', 'Treatment', 'Depth']] # Remove/add Round for including/excluding sequencing round
sample_meta = sample_meta.drop_duplicates(subset=['Unique'], keep='first')
sample_meta = sample_meta.reset_index(drop=True)
sample_meta.set_index('Unique', inplace=True)

#%% Create Gene_Meta_file for symbiosis Experiment
geneMeta = lotusCircDeep.T
colsToDrop = geneMeta.columns.to_list()

geneMeta = geneMeta.drop(columns=colsToDrop)
lotusCircRNAFiltered = lotusCircRNA.drop_duplicates(subset =['New_ID'], keep='first')

lotusCircRNAFiltered = lotusCircRNAFiltered.drop(columns=['chr', 'start', 'end', 'Round',
       'Sample_number', 'Treatment', 'Analysis', 'Tissue', 'Depth',
       'circRNA_ID', 'Repeat_overlap',
       'CIRI2_#junction_reads', 'CIRI2_SM_MS_SMS', 'CIRI2_#non_junction_reads',
       'CIRI2_junction_reads_ratio', 'CIRI2_gene_id2', 'strand',
       'CIRI2_junction_reads_ID', 'CIRI2_Product2', 'CLEAR_name',
       'CLEAR_score', 'CLEAR_exonCount', 'CLEAR_exonSizes',
       'CLEAR_exonOffsets', 'CLEAR_readNumber', 'CLEAR_isoformName',
       'CLEAR_index', 'CLEAR_flankIntron', 'CLEAR_FPBcirc', 'CLEAR_FPBlinear',
       'CLEAR_CIRCscore', 'Unique']) #'CIRI2_RPK', 'CLEAR_RPK', 'RPK', 'RPK_Sum_Sample','perMillScale', 'TPM', - add these for normalization

mergedGeneMeta = geneMeta.merge(lotusCircRNAFiltered, how ='left', left_index=True, right_on='New_ID')
mergedGeneMeta.set_index('New_ID', inplace=True)

#%% Begin object creation for pyWGCNA
allGeneExp = PyWGCNA.WGCNA(name = 'All data no norm mean filter round a', species='bacteria', geneExpPath='gene_exp.csv', outputPath='outpath', save=True)

#%% Perform initial analysis
allGeneExp.preprocess()
#%%
allGeneExp.findModules()
#%%
allGeneExp.updateSampleInfo(path = 'sample_meta.csv', sep = ',')

allGeneExp.setMetadataColor('Depth', {'Deep': 'deeppink', 'Shallow': 'darkviolet'})
allGeneExp.setMetadataColor('Treatment', {'C': 'thistle', 'M': 'violet', 'R': 'purple', 'A': 'magenta'})
# allGeneExp.setMetadataColor('Round', {'d': 'green', 'b': 'yellow', 'c': 'red', 'a': 'blue'})

#%%
allGeneExp.updateGeneInfo(path = '/gene_meta.csv', sep = ',')

#%%
allGeneExp.analyseWGCNA()
# allGeneExp.top_n_hub_genes(moduleName="brown", n=100)
#%%
allGeneExp.saveWGCNA()


# %%
pyOb = PyWGCNA.readWGCNA('data.p')

#%%
moduleOfInterest = ['lightcoral','dimgrey','white','snow','darkgrey','lightgrey','gainsboro','rosybrown']

#Below are the modules of interest for the different data
# All data from the non-normalized data
# ['black','lightcoral','darkred','gainsboro','seashell','salmon','indianred','sienna','whitesmoke','silver','coral','darkgrey','brown','darksalmon','rosybrown','firebrick','tomato']


for i in moduleOfInterest:
       module = pyOb.top_n_hub_genes(moduleName = i, n = 5000)
       module.to_csv('/geneList/module_' + i + '.csv')
# %%
