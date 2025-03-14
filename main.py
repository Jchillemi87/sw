# %%
import pandas as pd
import numpy as np
import os
import json

import importlib
import runes as r
importlib.reload(r)
import monsters as m
import monster_rune_pairing
importlib.reload(monster_rune_pairing)
from monster_rune_pairing import update_monster_priority,find_best_runes_for_monsters,find_best_monsters_for_all_runes

#json_path = 'C:/Users/p3057544/OneDrive - Charter Communications/Documents/sw/FractalParadox-35313848.json'
#json_path = 'C:/Users/Joseph/Desktop/Summoners War Exporter Files/FractalParadox-35313848.json'
json_path = 'FractalParadox-35313848.json'

# %% load data
with open(json_path, encoding='utf-8') as json_data:
    data = json.load(json_data)

my_monsters = m.load_my_monsters(data)
runes_df = r.load_runes(data)
r.check_hero_gem(runes_df)
runes_df['Total Rolls'] = runes_df[['Rolls ACC','Rolls CD','Rolls CR','Rolls ATK','Rolls DEF','Rolls HP','Rolls RES','Rolls SPD']].sum(axis=1)
reapp_targets = r.find_reapp_targets(runes_df)
maxed_runes = r.all_gem_grind_combinations(runes_df)

maxed_runes = r.get_rolls(maxed_runes)

my_monsters['name'] = my_monsters['name'].str.title()

# %% find_best_monsters_for_all_runes
monsters_prepared = update_monster_priority(my_monsters)

# %% tidy up and prepare rune_df for export
#runes_df = runes_df.rename(columns={'Rolls nan':'Total Rolls'})
#runes_df['Total Rolls'] = runes_df[['Rolls ACC','Rolls CD','Rolls CR','Rolls ATK','Rolls DEF','Rolls HP','Rolls RES','Rolls SPD']].sum(axis=1)
#excluding 'Rolls Flat Atk','Rolls Flat Def','Rolls Flat HP'

runes_df['set_id'] = runes_df['set_id'].str.upper() # standardized for consistency

# Ensure all necessary stat columns exist and fill missing values
for stat in ['HP', 'ATK', 'DEF', 'SPD', 'CR', 'CD', 'ACC', 'RES']:
    if stat not in runes_df.columns:
        runes_df[stat] = 0
    runes_df[stat].fillna(0, inplace=True)

# Handle Innate Stats
if 'Innate Stat' not in runes_df.columns:
    runes_df['Innate Stat'] = ''
else:
    runes_df['Innate Stat'] = runes_df['Innate Stat'].fillna('')

if 'Innate Stat Value' not in runes_df.columns:
    runes_df['Innate Stat Value'] = 0
else:
    runes_df['Innate Stat Value'] = runes_df['Innate Stat Value'].fillna(0)
# %% Get a Score for each rune
for stat in r.stat_list:
    column_name = 'Base '+stat
    runes_df[stat] = runes_df[column_name]

runes_df['Score'] = runes_df.apply(r.score_rune,axis=1)

# move 'Total Value' and 'Total Rolls' to the front of the dataframe
column_order_list = ['slot_no','set_id','main_stat_type','Score','SPD','Total Rolls']
runes_df = runes_df[column_order_list + [col for col in runes_df.columns if col not in column_order_list]]

# if gemmed is false, add 1 to Total Rolls
runes_df['Total Rolls'] = runes_df['Total Rolls'] + runes_df['Gemmed'].astype(int)

runes_df = runes_df.drop(columns=r.stat_list)

# find rolls percentile
maxed_runes_percentile = r.find_percentiles(maxed_runes.set_index('rune_id'),'New Total Rolls')

runes_df['Slot Rolls Percentile'] = maxed_runes_percentile.groupby(maxed_runes_percentile.index)['Slot Percentile'].max()
runes_df['Set Rolls Percentile'] = maxed_runes_percentile.groupby(maxed_runes_percentile.index)['Set Percentile'].max()

# find spd percentile
runes_spd_df = runes_df[runes_df['Base SPD']!=0].copy() # Only look at runes with SPD
runes_spd_percentile = r.find_percentiles(runes_spd_df,'Base SPD')
runes_spd_percentile = runes_spd_percentile.rename(columns={'Slot Percentile':'Slot SPD Percentile'
                                                            ,'Set Percentile':'Set SPD Percentile'})

runes_df = runes_df.join(runes_spd_percentile[['Slot SPD Percentile','Set SPD Percentile']])

# find score percentile
runes_score_percentile = r.find_percentiles(runes_df,'Score')
runes_score_percentile = runes_score_percentile.rename(columns={'Slot Percentile':'Slot Score Percentile'
                                                            ,'Set Percentile':'Set Score Percentile'})

runes_df = runes_df.join(runes_score_percentile[['Slot Score Percentile','Set Score Percentile']])

runes_df['Max Slot Percentile'] = runes_df[['Slot Score Percentile','Slot Rolls Percentile','Slot SPD Percentile']].max(axis=1)
runes_df['Max Set Percentile'] = runes_df[['Set Score Percentile','Set Rolls Percentile','Set SPD Percentile']].max(axis=1)

runes_df['Min Slot Percentile'] = runes_df[['Slot Score Percentile','Slot Rolls Percentile','Slot SPD Percentile']].min(axis=1)
runes_df['Min Set Percentile'] = runes_df[['Set Score Percentile','Set Rolls Percentile','Set SPD Percentile']].min(axis=1)

trash_great_runes_columns = ['slot_no'
                       ,'set_id'
                       ,'main_stat_type'
                       ,'Max Slot Percentile'
                       ,'Min Slot Percentile'
                       ,'Gemmed_Stat_Name'
                       ,'Max Hero Gem'
                       ,'Innate Stat'
                       ,'Innate Stat Value'
                       ,'Base SPD'
                       ,'Base CR'
                       ,'Base ACC'
                       ,'Base HP'
                       ,'Base ATK'
                       ,'Base DEF'
                       ,'Base CD'
                       ,'Base RES'
                       ,'Base Flat HP'
                       ,'Base Flat Atk'
                       ,'Base Flat Def'
                       ,'Max Set Percentile'
                       ,'Min Set Percentile'
                       ,'Slot Score Percentile'
                       ,'Set Score Percentile'
                       ,'Slot Rolls Percentile'
                       ,'Set Rolls Percentile'
                       ,'Slot SPD Percentile'
                       ,'Set SPD Percentile'
                       ,'Total Rolls'
                       ,'Score'
                       ,'grade'
                       ,'ancient']

trash_runes_columns = trash_great_runes_columns.copy()
trash_runes_columns.remove('Min Slot Percentile')
trash_runes_columns.remove('Min Set Percentile')
trash_runes_columns.remove('Gemmed_Stat_Name')
trash_runes_columns.remove('Max Hero Gem')
trash_runes_df = runes_df[trash_runes_columns]
trash_runes_df = trash_runes_df.sort_values(['slot_no','Max Slot Percentile'])

gem_targets_columns = trash_great_runes_columns.copy()
gem_targets_columns.remove('Max Slot Percentile')
gem_targets_columns.remove('Max Set Percentile')

gem_targets_df = runes_df[gem_targets_columns]
gem_targets_df = gem_targets_df[gem_targets_df['Max Hero Gem'] != True]
gem_targets_df = gem_targets_df.drop(columns=['Max Hero Gem'])

gem_targets_df.loc[gem_targets_df['Min Slot Percentile'] < gem_targets_df['Slot SPD Percentile'],'Min Slot Percentile'] = gem_targets_df[['Slot SPD Percentile','Min Slot Percentile']].max(axis=1, skipna=True)

gem_targets_df = gem_targets_df.sort_values(['set_id','Min Slot Percentile','slot_no'],ascending=[True,False,True])

# %% export runes_df,monsters_prepared,maxed_runes,best_monsters_for_runes,best_runes_for_monsters to excel
output_dir_path = os.path.dirname(os.path.abspath(__file__))

with pd.ExcelWriter(output_dir_path+'/runes.xlsx') as writer:
    runes_df.to_excel(writer,sheet_name='runes_df')
    monsters_prepared.to_excel(writer,sheet_name='monsters_prepared',index=False)
    maxed_runes.to_excel(writer,sheet_name='maxed_runes',index=False)
    reapp_targets.to_excel(writer,sheet_name='reapps',index=False)
    trash_runes_df.to_excel(writer,sheet_name='trash_runes',index=True)
    gem_targets_df.to_excel(writer,sheet_name='gem_targets',index=True)

# %%
# HIGH PRIORITY GLITCH: A rune's stat maybe recommended to be gemmed out if it's current value is equal to or lower than the max gemmed value + maxed grind value
# Example: Atk% with a base stat of 14 with a grind of 4 = 18 vs maxed hero gemmed Atk% of 11 + a max hero grind of 7 = 18

# pick a monster from my monsters and determine it's most desired stats
# note determine what % a flat stat gives compared to the it's percentage version for that monster
# starting with the main set for that monster, go through and grade each rune by slot
# note if slots 4 and 6 are hp and def, then limit the slot 4 and 6 to both hp and def runes instead of just 1
# when done, do the same for the offset set
# finally, grade all none used runes by slot as a "broken" set
# get a count of our monsters and keep the top x number of runes for each slots, and list out the remaining "bad runes" by lowest to highest score
# %%
r.score_rune(runes_df.loc[61599286895])
# %%

importlib.reload(r)
result_df = r.find_runes(runes_df
             ,sets=['VIOLENT','WILL']
             ,slot_2=['SPD']
             ,slot_4=['CD']
             ,slot_6=['HP']
             ,sub_stats=['SPD','HP','DEF','CD','Flat HP','ACC']
             )

graded_df = r.grade_runes_sub_stats(result_df
                          ,max_value=['SPD']
                          ,high_value=['HP']
                          ,some_value=['CD','Flat HP','ACC','DEF']
                          ,no_value=['CR'])

# Now graded_df has a 'grade_score' column that helps you pick the top runes.
graded_df.sort_values(['slot_no','grade_score'], ascending=[True,False], inplace=True)
graded_df.to_clipboard()
# %%
pd.set_option("display.max_columns", None)  # let Pandas show all columns
pd.set_option("display.width", 200)         # widen the console printout

print(graded_df[["grade_score"]].head(10))


# %%
