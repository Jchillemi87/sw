# %%
import pandas as pd
import numpy as np
import json

import importlib
import runes as r
from runes import stat_list, main_sets, off_sets
import monsters as m
importlib.reload(r)

#json_path = 'C:/Users/p3057544/OneDrive - Charter Communications/Documents/sw/FractalParadox-35313848.json'
#json_path = 'C:/Users/Joseph/Desktop/Summoners War Exporter Files/FractalParadox-35313848.json'
json_path = 'FractalParadox-35313848.json'
with open(json_path, encoding='utf-8') as json_data:
    data = json.load(json_data)

#GRADE_SETTING='legend' # Setting for gems and grinds

my_monsters = m.load_my_monsters(data)

# %%
runes_df = r.load_runes(data)
maxed_runes = r.all_gem_grind_combinations(runes_df)

my_monsters['name'] = my_monsters['name'].str.title()

#test_df = r.all_gem_grind_combinations(runes_df[runes_df.index == 37171789785])
#test_df

# %%

# Map slot to mainset column based on fixed and variable main stats
slot_to_column_mapping = {
    1: None,  # Slot 1 has a fixed main stat (Flat ATK)
    2: 'most_popular_slot2',
    3: None,  # Slot 3 has a fixed main stat (Flat DEF)
    4: 'most_popular_slot4',
    5: None,  # Slot 5 has a fixed main stat (Flat HP)
    6: 'most_popular_slot6'
}

def find_best_runes_for_monster(monster,runes):
    monster_preferences = monsters_prepared[monsters_prepared['name'] == monster].copy()
    
    best_runes_for_monster = pd.DataFrame()
    for slot, column in slot_to_column_mapping.items():
        # Use all sets for the slot
        filtered_runes = runes[(runes['slot_no'] == slot)]
        # Process main sets - matching on both set and main stat
        sets = off_sets
        # add main set to sets
        most_popular_mainset = monster_preferences['most_popular_mainset'].values[0]
        sets.append(most_popular_mainset)

        sets = filtered_runes[filtered_runes['set_id'].isin(sets)].copy()
        merged_sets = pd.DataFrame()
        if column:  # Variable main stat slots
            merged_sets = sets.merge(monster_preferences
                                     ,left_on='main_stat_type'
                                     ,right_on=column
                                     ,how='inner')
        else:  # Fixed main stat slots
            sets['key'] = 1
            monster_preferences['key'] = 1
            merged_sets = sets.merge(monster_preferences, on='key', how='inner')
            sets.drop('key', axis=1, inplace=True)
            merged_sets.drop('key', axis=1, inplace=True)

        merged_sets['hp_score'] = merged_sets['HP'] * merged_sets['HP_value']
        merged_sets['atk_score'] = merged_sets['ATK'] * merged_sets['ATK_value']
        merged_sets['def_score'] = merged_sets['DEF'] * merged_sets['DEF_value']
        merged_sets['spd_score'] = merged_sets['SPD'] * merged_sets['SPD_value']
        merged_sets['cr_score'] = merged_sets['CR'] * merged_sets['CR_value']
        merged_sets['cd_score'] = merged_sets['CD'] * merged_sets['CD_value']
        merged_sets['acc_score'] = merged_sets['ACC'] * merged_sets['ACC_value']
        merged_sets['res_score'] = merged_sets['RES'] * merged_sets['RES_value']
        merged_sets['Total Value'] = merged_sets[['hp_score','atk_score','def_score','spd_score','cr_score','cd_score','acc_score','res_score']].sum(axis=1)

        #keep only the highest value rune from the main set and 1 from off_sets
        best_main_set_rune = merged_sets[merged_sets['set_id']==most_popular_mainset].sort_values('Total Value',ascending=False).head(1)
        best_runes_for_monster = pd.concat([best_runes_for_monster, best_main_set_rune])

        best_main_set_rune = merged_sets[merged_sets['set_id'].isin(off_sets)].sort_values('Total Value',ascending=False).head(1)
        best_runes_for_monster = pd.concat([best_runes_for_monster, best_main_set_rune])

        # Process off_sets - matching only on main stat
    best_runes_for_monster = best_runes_for_monster.drop(columns=['key'])
    return best_runes_for_monster

def find_best_runes_for_monsters(monster_list,runes):
    # create an empty dataframe based on runes
    used_runes = runes.head(0).copy()
    results = []
    counter = 0
    for monster in monster_list:
        counter += 1
        print(monster,counter,'of',len(monster_list))
        #find best runes for monster excluding runes already used
        best_runes_for_monster = find_best_runes_for_monster(monster,runes[~runes['rune_id'].isin(used_runes['rune_id'])])
        results.append(best_runes_for_monster)
        #add best runes to used_runes
        used_runes = pd.concat([used_runes,best_runes_for_monster])

    return pd.concat(results)

def find_best_monster_for_rune(rune: str,monsters: pd.DataFrame):
    rune = maxed_runes[maxed_runes['rune_id'] == rune].copy()
    
    #fill HP, ATK, DEF, SPD, CR, CD, ACC, RES with 0 if they are nan
    rune[r.stat_list] = rune[r.stat_list].fillna(0)

    # if the rune is in main_sets rune, then only consider monsters that have the same main set
    if rune['set_id'].values[0] in main_sets:
        monsters = monsters[monsters['most_popular_mainset'] == rune['set_id'].values[0]].copy()        

    column = slot_to_column_mapping[rune['slot_no'].values[0]]
    if column:
        monsters = monsters[monsters[column] == rune['main_stat_type'].values[0]].copy()
    else:
        monsters = monsters[monsters['most_popular_mainset'] == rune['set_id'].values[0]].copy()

    rune['key'] = 1
    monsters['key'] = 1
    rune = rune.merge(monsters,on='key',how='inner')

    rune['hp_score'] = rune['HP'] * rune['HP_value']
    rune['atk_score'] = rune['ATK'] * rune['ATK_value']
    rune['def_score'] = rune['DEF'] * rune['DEF_value']
    rune['spd_score'] = rune['SPD'] * rune['SPD_value']
    rune['cr_score'] = rune['CR'] * rune['CR_value']
    rune['cd_score'] = rune['CD'] * rune['CD_value']
    rune['acc_score'] = rune['ACC'] * rune['ACC_value']
    rune['res_score'] = rune['RES'] * rune['RES_value']
    rune['Total Value'] = rune[['hp_score','atk_score','def_score','spd_score','cr_score','cd_score','acc_score','res_score']].sum(axis=1)
    rune = rune.sort_values('Total Value',ascending=False)

    rune = rune.drop(columns=['key'])
    
    return rune.head(1)

def find_best_monsters_for_all_runes(rune_list,monsters):
    results = []
    counter = 0
    for rune in rune_list:
        counter += 1
        print(rune,counter,'of',len(rune_list))
        results.append(find_best_monster_for_rune(rune,monsters))
    return pd.concat(results)
# %%
def update_monster_priority():
    monster_priority = pd.read_csv('monster_priority.csv')
    monster_priority = monster_priority.drop_duplicates(subset=['name'],keep='first')

    clean_up_columns = ['primary sets','off sets','slot 2s','slot 4s','slot 6s','subs high priority','subs normal priority']
    for col in clean_up_columns:
        monster_priority[col] = monster_priority[col].str.strip()
        monster_priority[col] = monster_priority[col].str.replace(' ', '')
        monster_priority[col] = monster_priority[col].str.upper()
    
    # ### REMOVE ###
    clean_up_columns = ['primary sets','off sets','slot 2s','slot 4s','slot 6s']
    for col in clean_up_columns:
        monster_priority[col] = monster_priority[col].str.split(',').str.get(0)
    
    monster_priority['off sets'] = monster_priority['off sets'].str.replace('UNKNOWN','')

    # Prepare monster data for merging
    monsters_prepared = my_monsters[['name'
                                    ,'top_4_sub_stats'
                                    ,'most_popular_slot2'
                                    ,'most_popular_slot4'
                                    ,'most_popular_slot6'
                                    ,'most_popular_mainset'
                                    ,'most_popular_offset'
                                    ,'HP_value'
                                    ,'ATK_value'
                                    ,'DEF_value'
                                    ,'SPD_value'
                                    ,'CR_value'
                                    ,'CD_value'
                                    ,'ACC_value'
                                    ,'RES_value']].copy()
    
    monster_priority = monster_priority.rename(columns={'slot 2s':'most_popular_slot2'
                                                        ,'slot 4s':'most_popular_slot4'
                                                        ,'slot 6s':'most_popular_slot6'
                                                        ,'primary sets':'most_popular_mainset'
                                                        ,'off sets':'most_popular_offset'})
    
    column_update_list = ['most_popular_mainset'
                          ,'most_popular_slot2'
                          ,'most_popular_slot4'
                          ,'most_popular_slot6']

    monster_priority = monster_priority.dropna(subset=column_update_list,how='any').astype({'most_popular_mainset':str
                                                                                            ,'most_popular_slot2':str
                                                                                            ,'most_popular_slot4':str
                                                                                            ,'most_popular_slot6':str})

    monsters_prepared.set_index('name').update(monster_priority.set_index('name')[column_update_list]
                                                                   ,overwrite=True
                                                                   ,errors='ignore')

    # add 'top_4_sub_stats' from monster_prepared to monster_priority based on name
    #monster_priority = monster_priority.set_index('name').join(monsters_prepared.set_index('name')['top_4_sub_stats']).reset_index()
    return monsters_prepared

monsters_prepared = update_monster_priority()
best_monsters_for_runes = find_best_monsters_for_all_runes(runes_df.index.tolist(),monsters_prepared)
best_monsters_for_runes = best_monsters_for_runes.sort_values('Total Value',ascending=False)


# %%
monsters = my_monsters.dropna(subset=['top_4_sub_stats'])
monsters = monsters['name'].tolist()

columns_of_interest= best_monsters_for_runes.columns[best_monsters_for_runes.columns.isin(maxed_runes.columns)]
best_runes_for_monsters = find_best_runes_for_monsters(monsters,runes=best_monsters_for_runes[columns_of_interest])
best_runes_for_monsters = best_runes_for_monsters.sort_values('Total Value',ascending=True)

#Drop HP	ATK	DEF	SPD	CR	CD	ACC	RES
#Drop HP_value	ATK_value	DEF_value	SPD_value	CR_value	CD_value	ACC_value	RES_value
#Drop hp_score	atk_score	def_score	spd_score	cr_score	cd_score	acc_score	res_score
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
# %%
# get location of current .py file
import os
output_dir_path = os.path.dirname(os.path.abspath(__file__))

runes_df = runes_df.reset_index()
runes_df = runes_df.merge(my_monsters[['unit_id','name']].rename(columns={'name':'location'})
               ,left_on='occupied_id'
               ,right_on='unit_id'
               ,how='left').drop(columns='unit_id')

runes_df.set_index('rune_id',inplace=True)

runes_df = runes_df.join(best_monsters_for_runes[['rune_id','Total Value']].set_index('rune_id'))

# %%
def get_rolls(runes_df):
    runes_df['New Total Rolls'] = 0
    for stat in r.stat_list:
        runes_df['New Total Rolls'] = runes_df['New Total Rolls'] + runes_df[stat].fillna(0)/r.stat_roles[stat]
    return runes_df

best_monsters_for_runes = get_rolls(best_monsters_for_runes)

# add 'New Total Rolls' from best_monsters_for_runes to runes_df
runes_df = runes_df.join(best_monsters_for_runes.set_index('rune_id')[['New Total Rolls']])

# %%
# add Total Rolls to runes_df and best_monsters_for_runes
runes_df = runes_df.rename(columns={'Rolls nan':'Total Rolls'})
runes_df['Total Rolls'] = runes_df[['Rolls ACC','Rolls CD','Rolls CR','Rolls ATK','Rolls DEF','Rolls HP','Rolls RES','Rolls SPD']].sum(axis=1)
#excluding 'Rolls Flat Atk','Rolls Flat Def','Rolls Flat HP'

######################################################## 
# (1) Standardize `set_id` and `main_stat_type` for consistency
########################################################
runes_df['set_id'] = runes_df['set_id'].str.upper()

########################################################
# (3) Ensure all necessary stat columns exist and fill missing values
########################################################
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
# %%
runes_df['HP'] = runes_df['Base HP']
runes_df['ATK'] = runes_df['Base ATK']
runes_df['DEF'] = runes_df['Base DEF']
runes_df['SPD'] = runes_df['Base SPD']
runes_df['CR'] = runes_df['Base CR']
runes_df['CD'] = runes_df['Base CD']
runes_df['ACC'] = runes_df['Base ACC']
runes_df['RES'] = runes_df['Base RES']

runes_df['Score'] = runes_df.apply(r.score_rune,axis=1)

# move 'Total Value' and 'Total Rolls' to the front of the dataframe
column_order_list = ['slot_no','set_id','main_stat_type','Score','Total Value','Total Rolls','New Total Rolls','SPD','location']
runes_df = runes_df[column_order_list + [col for col in runes_df.columns if col not in column_order_list]]

# if gemmed is false, add 1 to Total Rolls
runes_df['Total Rolls'] = runes_df['Total Rolls'] + runes_df['Gemmed'].astype(int)
# %%
# export runes_df,monsters_prepared,maxed_runes,best_monsters_for_runes,best_runes_for_monsters to excel
with pd.ExcelWriter(output_dir_path+'/runes.xlsx') as writer:
    runes_df.to_excel(writer,sheet_name='runes_df')
    monsters_prepared.to_excel(writer,sheet_name='monsters_prepared',index=False)
    #maxed_runes.to_excel(writer,sheet_name='maxed_runes',index=False)
    best_monsters_for_runes.to_excel(writer,sheet_name='best_monsters_for_runes',index=False)
    best_runes_for_monsters.to_excel(writer,sheet_name='best_runes_for_monsters',index=True)

# %%
# get a list of all monsters from my_monsters that don't have nan in top_4_sub_stats
monsters = my_monsters.dropna(subset=['top_4_sub_stats'])
monsters = monsters['name'].tolist()

results = find_best_runes_for_monsters(monsters,maxed_runes)
results = results.drop_duplicates(subset='rune_id')
# %%
runes_df['useful'] = False
runes_df['useful'] = runes_df.index.drop_duplicates().isin(results['rune_id'])
result_columns_of_interest = ['name','Total Value','Suggested Gem In','Suggested Gem Out']
rune_monster_analysis = runes_df.drop(columns=[col for col in runes_df.columns if col in result_columns_of_interest]).join(results.set_index('rune_id')[result_columns_of_interest])
rune_monster_analysis
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