# %%
import pandas as pd

import runes as r
from runes import stat_list, main_sets, off_sets
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

def find_best_runes_for_monster(monster,monsters,runes):
    monster_preferences = monsters[monsters['name'] == monster['name']].copy()
    
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

# this function is terrible and needs to be re-written
def find_best_runes_for_monsters(monsters,runes):
    # create an empty dataframe based on runes
    used_runes = runes.head(0).copy()
    results = []
    counter = 0
    for index,monster_row in monsters.iterrows():
        counter += 1
        print(monster_row['name'],counter,'of',len(monsters))
        #find best runes for monster excluding runes already used
        best_runes_for_monster = find_best_runes_for_monster(monster_row
                                                             ,monsters
                                                             ,runes[~runes['rune_id'].isin(used_runes['rune_id'])])
        results.append(best_runes_for_monster)
        #add best runes to used_runes
        used_runes = pd.concat([used_runes.infer_objects(),best_runes_for_monster.infer_objects()])
        #infer_objects fixes a weird bug with pandas version 1.5 (https://stackoverflow.com/questions/73800841/add-series-as-a-new-row-into-dataframe-triggers-futurewarning)

    return pd.concat(results)

def find_best_monster_for_rune(rune,monsters):
    
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

def find_best_monsters_for_all_runes(maxed_runes,monsters):
    rune_list = maxed_runes['rune_id'].drop_duplicates().tolist()
    results = []
    counter = 0
    for rune in rune_list:
        counter += 1
        print(rune,counter,'of',len(rune_list))
        rune_copy = maxed_runes[maxed_runes['rune_id'] == rune].copy()
        results.append(find_best_monster_for_rune(rune_copy,monsters))
    return pd.concat(results)

def update_monster_priority(my_monsters):
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

def get_rolls(runes_df):
    runes_df['New Total Rolls'] = 0
    for stat in r.stat_list:
        runes_df['New Total Rolls'] = runes_df['New Total Rolls'] + runes_df[stat].fillna(0)/r.stat_roles[stat]
    return runes_df

# %%