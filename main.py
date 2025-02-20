# %%
import pandas as pd
import numpy as np
import os
import json

import importlib
import runes as r
importlib.reload(r)
import monsters as m
import rune_optimizer
importlib.reload(rune_optimizer)
from rune_optimizer import update_monster_priority,find_best_runes_for_monsters,find_best_monsters_for_all_runes,get_rolls

#json_path = 'C:/Users/p3057544/OneDrive - Charter Communications/Documents/sw/FractalParadox-35313848.json'
#json_path = 'C:/Users/Joseph/Desktop/Summoners War Exporter Files/FractalParadox-35313848.json'
json_path = 'FractalParadox-35313848.json'

# %% load data
with open(json_path, encoding='utf-8') as json_data:
    data = json.load(json_data)

my_monsters = m.load_my_monsters(data)
runes_df = r.load_runes(data)
maxed_runes = r.all_gem_grind_combinations(runes_df)
my_monsters['name'] = my_monsters['name'].str.title()

# %% find_best_monsters_for_all_runes
monsters_prepared = update_monster_priority(my_monsters)
best_monsters_for_runes = find_best_monsters_for_all_runes(maxed_runes,monsters_prepared)
best_monsters_for_runes = best_monsters_for_runes.sort_values('Total Value',ascending=False)

# %% find_best_runes_for_monsters
monsters = my_monsters.dropna(subset=['top_4_sub_stats'])
columns_of_interest= best_monsters_for_runes.columns[best_monsters_for_runes.columns.isin(maxed_runes.columns)]
best_runes_for_monsters = find_best_runes_for_monsters(monsters,runes=best_monsters_for_runes[columns_of_interest])

best_runes_for_monsters = best_runes_for_monsters.sort_values('Total Value',ascending=True)
best_runes_for_monsters = best_runes_for_monsters.drop(columns=['HP','ATK','DEF','SPD','CR','CD','ACC','RES'
                                                                ,'HP_value','ATK_value','DEF_value','SPD_value','CR_value','CD_value','ACC_value','RES_value'
                                                                ,'hp_score','atk_score','def_score','spd_score','cr_score','cd_score','acc_score','res_score'])
best_runes_for_monsters = best_runes_for_monsters.set_index('rune_id').join(runes_df[['Base SPD'
                                                                                     ,'Base CR'
                                                                                     ,'Base HP'
                                                                                     ,'Base ATK'
                                                                                     ,'Base DEF'
                                                                                     ,'Base ACC'
                                                                                     ,'Base CD'
                                                                                     ,'Base RES'
                                                                                     ,'Base Flat HP'
                                                                                     ,'Base Flat Atk'
                                                                                     ,'Base Flat Def'
                                                                                     ]])
# %% Add Append Total Value and New Total Rolls to runes dataframe
runes_df = runes_df.reset_index()
runes_df = runes_df.merge(my_monsters[['unit_id','name']].rename(columns={'name':'location'})
               ,left_on='occupied_id'
               ,right_on='unit_id'
               ,how='left').drop(columns='unit_id')

runes_df.set_index('rune_id',inplace=True)
runes_df = runes_df.join(best_monsters_for_runes[['rune_id','Total Value']].set_index('rune_id'))

# add Total Rolls to runes_df and best_monsters_for_runes
best_monsters_for_runes = get_rolls(best_monsters_for_runes)
runes_df = runes_df.join(best_monsters_for_runes.set_index('rune_id')[['New Total Rolls']])

# %%
runes_df = runes_df.rename(columns={'Rolls nan':'Total Rolls'})
runes_df['Total Rolls'] = runes_df[['Rolls ACC','Rolls CD','Rolls CR','Rolls ATK','Rolls DEF','Rolls HP','Rolls RES','Rolls SPD']].sum(axis=1)
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
column_order_list = ['slot_no','set_id','main_stat_type','Score','Total Value','Total Rolls','New Total Rolls','SPD','location']
runes_df = runes_df[column_order_list + [col for col in runes_df.columns if col not in column_order_list]]

# if gemmed is false, add 1 to Total Rolls
runes_df['Total Rolls'] = runes_df['Total Rolls'] + runes_df['Gemmed'].astype(int)

runes_df = runes_df.drop(columns=r.stat_list)

# %%
# export runes_df,monsters_prepared,maxed_runes,best_monsters_for_runes,best_runes_for_monsters to excel
output_dir_path = os.path.dirname(os.path.abspath(__file__))

with pd.ExcelWriter(output_dir_path+'/runes.xlsx') as writer:
    runes_df.to_excel(writer,sheet_name='runes_df')
    monsters_prepared.to_excel(writer,sheet_name='monsters_prepared',index=False)
    #maxed_runes.to_excel(writer,sheet_name='maxed_runes',index=False)
    best_monsters_for_runes.to_excel(writer,sheet_name='best_monsters_for_runes',index=False)
    best_runes_for_monsters.to_excel(writer,sheet_name='best_runes_for_monsters',index=True)

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