# %%
GRADE_SETTING='hero' # Setting for gems and grinds

import pandas as pd

stat_list = ['HP','ATK','DEF','SPD','CR','CD','ACC','RES']

main_sets = ['VIOLENT','SWIFT', 'RAGE', 'FATAL', 'DESPAIR', 'VAMPIRE']
off_sets = ['BLADE','ENERGY','GUARD','FOCUS','ENDURE','ENHANCE','WILL','SHIELD','REVENGE','NEMESIS','DESTROY','FIGHT','DETERMINATION','ACCURACY','TOLERANCE','SEAL','INTANGIBLE']

gems_and_grinds_dict = {
    'type': ['gem', 'gem', 'grind', 'grind'],
    'grade': ['legend', 'hero', 'legend', 'hero'],
    'ACC': [11, 9, 0, 0],
    'CD': [10, 8, 0, 0],
    'CR': [9, 7, 0, 0],
    'Flat Atk': [40, 30, 30, 22],
    'Flat Def': [40, 30, 30, 22],
    'Flat HP': [580, 420, 550, 450],
    'ATK': [13, 11, 10, 7],
    'DEF': [13, 11, 10, 7],
    'HP': [13, 11, 10, 7],
    'RES': [11, 9, 0, 0],
    'SPD': [10, 8, 5, 4]
}

# To create a DataFrame from this dictionary:
gems_and_grinds = pd.DataFrame(gems_and_grinds_dict)

stat_roles = {'ACC':8,'CR':6,'Flat Atk':20,'ATK':8,'CD':7,'SPD':6,'Flat HP':375,'HP':8,'Flat Def':20,'DEF':8,'RES':8}
max_stats_dic = {'ACC':40,'CR':30,'Flat Atk':100,'ATK':40,'CD':35,'SPD':30,'Flat HP':1875,'HP':40,'Flat Def':10,'DEF':40,'RES':40}
main_stat_max = {'ACC':64,'CR':58,'Flat Atk':160,'ATK':63,'CD':80,'SPD':42,'Flat HP':2448,'HP':63,'Flat Def':160,'DEF':63,'RES':64}

# Rune slot restrictions for substats.
impossible_sub_stats = {
    'Flat ATK': [1, 3],
    'ATK': [3],
    'Flat Def': [1, 3],
    'DEF': [1],
    'Flat HP': [5]
}

# Legendary grind bonus values.
# For percentage stats, these are given in percentage points.
grind = {
    "legend": {
        "SPD": 5,     # flat bonus for SPD
        "ATK": 10,    # bonus %ATK (for percentage-based ATK)
        "HP": 10,     # bonus %HP
        "DEF": 10,    # bonus %DEF
        "Flat Atk": 30,
        "Flat Def": 30,
        "Flat HP": 550,
        "ACC": 0,
        "RES": 0
    }
}

set_id_dict = {
    1: 'ENERGY',
    2: 'GUARD',
    3: 'SWIFT',
    4: 'BLADE',
    5: 'RAGE',
    6: 'FOCUS',
    7: 'ENDURE',
    8: 'FATAL',
    9: '',
    10: 'DESPAIR',
    11: 'VAMPIRE',
    12: '',
    13: 'VIOLENT',
    14: 'NEMESIS',
    15: 'WILL',
    16: 'SHIELD',
    17: 'REVENGE',
    18: 'DESTROY',
    19: 'FIGHT',
    20: 'DETERMINATION',
    21: 'ENHANCE',
    22: 'ACCURACY',
    23: 'TOLERANCE',
    24: 'SEAL',
    25: 'INTANGIBLE'
}

stat_dict = {
    1:'Flat HP'
    ,2:'HP'
    ,3:'Flat Atk'
    ,4:'ATK'
    ,5:'Flat Def'
    ,6:'DEF'
    ,8:'SPD'
    ,9:'CR'
    ,10:'CD'
    ,11:'RES'
    ,12:'ACC'
}

def load_runes(data):
    runes = pd.DataFrame.from_dict(data['runes'])
    equipt_runes = pd.json_normalize(data['unit_list'],record_path=['runes'])
    #runes = pd.json_normalize(data.loc['runes'].values[0])
    runes = pd.concat([runes,equipt_runes])

    dropCols=['occupied_type'
    #,'wizard_id'
    #,'occupied_id'
    ,'upgrade_limit']

    grade_id_dict = {3:'rare'
        ,4:'hero'
        ,5:'legendary'}

    renameCols={'upgrade_curr':'level'
                ,'class':'stars'
                ,'pri_eff':'main_stat'
                ,'prefix_eff':'innate'
                ,'extra':'grade'}    
    
    runes = runes.drop(dropCols,axis=1).rename(columns=renameCols)

    # check for anciant runes
    runes['ancient'] = runes['grade'] > 10
    runes.loc[runes['ancient'],'grade'] -= 10

    runes['set_id'] = runes['set_id'].map(set_id_dict)
    runes['grade'] = runes['grade'].map(grade_id_dict)

    runes = runes.set_index('rune_id')

    runes_main_stat = pd.DataFrame(runes['main_stat'].tolist(),columns=['main_stat_type','main_stat_value'],index=runes.index)
    runes_main_stat['main_stat_type']= runes_main_stat['main_stat_type'].map(stat_dict)
    runes = runes.join(runes_main_stat)

    # Innrate
    runeInnates = pd.DataFrame(runes['innate'].to_list(),columns=['Stat','Base'],index=runes.index)
    runeInnates['Stat']= runeInnates['Stat'].map(stat_dict)
    runeInnates['Rolls']= runeInnates['Base']/runeInnates['Stat'].map(stat_roles)
    runes = runes.join(runeInnates)


    rune_stats = pd.DataFrame(runes['sec_eff'].explode().to_list(),columns=['Stat','Base','Gemmed','Grind'],index=runes['sec_eff'].explode().index)
    rune_stats['Stat']= rune_stats['Stat'].map(stat_dict)
    rune_stats['Rolls'] = rune_stats['Base']/rune_stats['Stat'].map(stat_roles)
    rune_stats.loc[rune_stats['Rolls']< 0,'Rolls'] = 0
    rune_base_stats = pd.concat([rune_stats,runeInnates])
    rune_base_stats = rune_base_stats.pivot(columns='Stat')

    #Clean up Base Stats
    rune_base_stat_columns = rune_base_stats['Base'].columns[rune_base_stats['Base'].columns.notna()]
    rune_base_stats_clean = rune_base_stats['Base'][rune_base_stat_columns]
    rune_stat_rolls_columns = rune_base_stats['Rolls'].columns[rune_base_stats['Rolls'].columns.notna()]
    rune_stat_rolls_clean = rune_base_stats['Rolls'][rune_stat_rolls_columns]
    rune_stat_rolls_clean = rune_stat_rolls_clean.add_suffix(' Rolls')
    rune_stat_rolls_clean['Total_Rolls']= rune_base_stats['Rolls'].sum(axis=1)

    #round all columns to nearest zero except 'Total_Rolls'
    rune_stat_rolls_clean.update(rune_stat_rolls_clean.loc[:,
    rune_stat_rolls_clean.columns
    != 'Total_Rolls'].round(),
    errors='ignore')

    columns_to_keep = ['slot_no','set_id','main_stat_type','main_stat_value','level','occupied_id','grade','ancient']
    
    runes = runes[columns_to_keep].join(rune_base_stats_clean).join(rune_stat_rolls_clean)
    runes['Missing_Rolls']= (4- runes['level'].astype(int)/3).astype(int)
    runes.loc[runes['Missing_Rolls']< 0,'Missing_Rolls'] = 0

    runes['Efficiency']= (runes['Total_Rolls']+ runes['Missing_Rolls'])/10
    runes_main_stat['main_stat_value']= runes_main_stat['main_stat_type'].map(main_stat_max)
    runes = runes.fillna(runes_main_stat.pivot(columns='main_stat_type')['main_stat_value'])

    runes.iloc[:,5:len(runes.columns)-2]= runes.iloc[:,5:len(runes.columns)-2]#.astype(int)
    runes['SPD Rank']= runes.groupby(['slot_no','set_id','main_stat_type'])['SPD'].rank(method="dense",ascending=False)
    runes['CR Rank']= runes.groupby(['slot_no','set_id','main_stat_type'])['CR'].rank(method="dense",ascending=False)
    runes = runes.sort_values(['set_id','SPD Rank','main_stat_type','slot_no'])
    first_col = runes.pop('SPD Rank')
    runes.insert(0,'SPD Rank',first_col)
    #runes.to_clipboard()

    # create a clean runes df
    # Took out ,'Spd','Spd Rolls','Crit Rate','Crit Rate Rolls','Efficiency','Missing_Rolls' from runes_df to keep it cleaner
    runes_df = runes[columns_to_keep]
    runeInnates = runeInnates.rename(columns={'Stat':'Innate Stat'
                                              ,'Base':'Innate Stat Value'
                                              ,'Rolls':'Innate Stat Rolls'})
    runes_df = runes_df.join(runeInnates)
    # remove rune_base_stats's multi column index
    rune_base_stats_1_level = rune_base_stats['Base'].add_prefix('Base ').join(rune_base_stats['Gemmed'].add_prefix('Gemmed ')).join(rune_base_stats['Grind'].add_prefix('Grinded ')).join(rune_base_stats['Rolls'].add_prefix('Rolls '))
    drop_cols = ['Base nan','Gemmed nan','Grinded nan','Rolls nan','Grinded ACC','Grinded CD','Grinded CR','Grinded RES']
    rune_base_stats_1_level = rune_base_stats_1_level.drop(columns=drop_cols)
    runes_df = runes_df.join(rune_base_stats_1_level)
    runes_df

    # check if any of the "Gemmed" stats are already gemmed (check if value is 1)
    runes_df['Gemmed']= 0
    runes_df['Gemmed']= runes_df[['Gemmed ACC', 'Gemmed CD', 'Gemmed CR', 'Gemmed Flat Atk', 'Gemmed Flat Def', 'Gemmed Flat HP', 'Gemmed ATK', 'Gemmed DEF', 'Gemmed HP', 'Gemmed RES', 'Gemmed SPD']].sum(axis=1)
    runes_df['Gemmed']= runes_df['Gemmed'].astype(int).astype(bool)
    runes_df.loc[runes_df[runes_df['Gemmed']].index,'Gemmed_Stat_Name'] = runes_df[['Gemmed ACC','Gemmed CD', 'Gemmed CR', 'Gemmed Flat Atk', 'Gemmed Flat Def', 'Gemmed Flat HP', 'Gemmed ATK', 'Gemmed DEF', 'Gemmed HP', 'Gemmed RES', 'Gemmed SPD']].idxmax(axis=1)
    runes_df['Gemmed_Stat_Name']= runes_df['Gemmed_Stat_Name'].fillna('')
    runes_df['Gemmed_Stat_Name']= runes_df['Gemmed_Stat_Name'].str.replace('Gemmed ','')
    return runes_df

def grind_runes(df,grade=GRADE_SETTING):
    runes_df = df.copy()
    legend_grinds = gems_and_grinds[(gems_and_grinds['type'] == 'grind') & (gems_and_grinds['grade'] == grade)][['Flat Atk','Flat Def','Flat HP','ATK','DEF','HP','SPD']]
    for stat in legend_grinds.columns:
        runes_df.loc[(runes_df['Base '+ stat] > 0) | (runes_df['New '+ stat] > 0) , 'Grinded '+stat] = legend_grinds.iloc[0][stat]
    return runes_df

def get_new_stats(df):
    runes_df = df.copy()

    base_stats_columns = [col for col in runes_df.columns if 'Base ' in col]
    base_stats_columns.sort()
    base_stats_columns

    new_stats_columns = [col for col in runes_df.columns if 'New ' in col]
    new_stats_columns.sort()
    new_stats_columns


    #[string.replace('Gemmed','Base') for string in gemmed_stats_columns]
    new_runes_df = runes_df[new_stats_columns].copy()
    new_runes_df.columns = [string.replace('New','Base') for string in new_runes_df.columns]

    runes_df.update(new_runes_df)

    runes_df = runes_df.reset_index()
    
    for stat in ['Flat Atk','Flat Def','Flat HP','ATK','DEF','HP','SPD']:
        # only add grinded stats to runes that have a base stat
        runes_df.loc[runes_df['Base '+ stat] > 0 , 'New ' + stat] = runes_df['Base '+ stat] + runes_df['Grinded ' + stat]

    return runes_df

def all_gem_grind_combinations(runes_df):
    runes_with_all_gems = []
    gem_max_rolls = gems_and_grinds.loc[(gems_and_grinds['type']=='gem') & (gems_and_grinds['grade']==GRADE_SETTING)].drop(columns=['type','grade'])
    
    #fill na from 'Base ' + stat_dict.values() with 0
    runes_df[['Base '+stat for stat in stat_dict.values()]] = runes_df[['Base '+stat for stat in stat_dict.values()]].fillna(0)

    def filter_runes(stat,df):
        # exclude runes that have the stat as their main stat
        df = df[df['main_stat_type'] != stat]

        #exclude runes that have the stat as an Innate Stat
        df = df[df['Innate Stat'] != stat]

        # exclude slots that can't have the stat
        if stat in ['DEF','Flat Def','Flat Atk']:
            df = df[df['slot_no'] != 1]

        if stat in ['ATK','Flat Def','Flat Atk']:
            df = df[df['slot_no'] != 3]

        if stat == 'Flat HP':
            df = df[df['slot_no'] != 5]

        return df

    for gem_out_stat in stat_dict.values():
        # exclude runes that don't have the gem_out_stat in their subs
        runes_with_gem_out_stat = runes_df[runes_df['Base '+gem_out_stat] > 0.0].copy() #check to see why we also were exluding runes that had an NA value for the stat

        # only include runes that have no gem or have the current gem_out_stat as their gem (example: we can't gem out ATK if we have already gemmed in HP)
        runes_with_gem_out_stat = runes_with_gem_out_stat[(~runes_with_gem_out_stat['Gemmed']) | (runes_with_gem_out_stat['Gemmed_Stat_Name'] == gem_out_stat)]

        runes_with_gem_out_stat = filter_runes(gem_out_stat,runes_with_gem_out_stat)
    
        for gem_in_stat in stat_dict.values():
            runes_with_new_gemmed_stat = filter_runes(gem_in_stat,runes_with_gem_out_stat)

            # exclude any runes where the stat is equal or higher to the max roll of our current gem grade
            runes_with_new_gemmed_stat = runes_with_new_gemmed_stat[runes_with_new_gemmed_stat['Base '+gem_in_stat] < gem_max_rolls.iloc[0][gem_in_stat]]
            
            runes_with_new_gemmed_stat['New '+gem_out_stat] = 0 # set the new value of the original stat to 0
            runes_with_new_gemmed_stat['Suggested Gem Out'] = gem_out_stat
            runes_with_new_gemmed_stat['Suggested Gem In'] = ''
            runes_with_new_gemmed_stat['Logic']= ''
            runes_with_new_gemmed_stat['Suggested Gem In'] = gem_in_stat
            new_stat_value = gem_max_rolls.iloc[0][gem_in_stat]
            runes_with_new_gemmed_stat['New '+gem_max_rolls[gem_in_stat].name] = new_stat_value
            runes_with_new_gemmed_stat['Logic']= f'Gem In {new_stat_value} {gem_in_stat} Over {gem_out_stat}'
            runes_with_all_gems.append(runes_with_new_gemmed_stat)

    runes_with_all_gems = pd.concat(runes_with_all_gems).reset_index()

    runes_with_all_gems_main_stat = runes_with_all_gems.drop(columns=['main_stat_type','Innate Stat']).set_index('rune_id').join(runes_df[['main_stat_type','Innate Stat']])
       
    runes_with_all_gems_and_max_grinds = grind_runes(runes_with_all_gems_main_stat)

    runes_with_all_gems_and_max_grinds = get_new_stats(runes_with_all_gems_and_max_grinds)
    #HP_value   ATK_value   DEF_value   SPD_value   CR_value    CD_value    ACC_value   RES_value
    
    maxed_runes = runes_with_all_gems_and_max_grinds.rename(columns={
        'New HP':'HP'
        ,'New ATK':'ATK'
        ,'New DEF':'DEF'
        ,'New SPD':'SPD'
        ,'Base CR':'CR'
        ,'Base CD':'CD'
        ,'Base ACC':'ACC'
        ,'Base RES':'RES'
    })[['set_id','slot_no','main_stat_type','rune_id','Gemmed_Stat_Name','Suggested Gem In','Suggested Gem Out','HP','ATK','DEF','SPD','CR','CD','ACC','RES']]
    return maxed_runes

popular_sets = ['VIOLENT','SWIFT','WILL','DESPAIR','INTANGIBLE']
other_sets = ['REVENGE','RAGE','FIGHT','SEAL','BLADE','FOCUS','NEMESIS','DESTROY']

def score_rune(row): 
    """
    Calculates the rune's score using the updated framework:
      - Ignore flat sub stats (they contribute 0).
      - Convert each non-flat sub stat to a raw roll count (value / stat_roles).
      - If >=3 raw rolls, confirm it meets the efficiency threshold:
          3-roll => >= 3 * max_roll * 0.95
          4-roll => >= 4 * max_roll * 0.90
        Otherwise, reduce to 2.x so it doesn't get the multi-roll bonus.
      - Add the 'desired stat bonus' (Speed=+1.5, HP/ATK/CR/ACC=+1, DEF/RES/CD=+0.5, else=0).
      - If final roll count >= 3, add +1 for each roll above 2 (3-roll=+1, 4-roll=+2, etc.).
      - Innate penalty of -0.5 if a grindable innate is present.
      - Slot-based bonuses/penalties.
      - Set-based bonuses/penalties.
    """

    desired_bonus = {
        'HP': 1, # HP%  
        'ATK': 1, # ATK%  
        'DEF': 0.5, # DEF%  
        'SPD': 1.5, # Speed
        'CR': 1,
        'CD': 0.5,
        'ACC': 1,
        'RES': 0.5,
    }
    
    # Check if set is popular, other, or less desired
    # (Script’s own dictionaries: popular_sets, other_sets)
    set_name = str(row['set_id'])
    if set_name in popular_sets:
        set_bonus = 1
    elif set_name in other_sets:
        set_bonus = 0
    else:
        set_bonus = -1

    # --------------------------------------------------------
    # B) Base Score from Sub Stats
    # --------------------------------------------------------
    total_score = 0.0

    for stat in stat_list:
        # Grab the sub stat value from columns (HP, ATK, DEF, SPD, CR, CD, ACC, RES)
        # The DataFrame from all_gem_grind_combinations renamed these to capital letters:
        value = row.get(stat, 0)
        if not value or value <= 0:
            # no sub stat or it's 0 => skip
            continue
        
        # 1) Find raw roll count
        max_roll = stat_roles.get(stat, 0)
        if max_roll == 0:
            # Flat stats or unknown => no contribution
            continue
        
        raw_roll_count = value / max_roll

        # 2) Check thresholds for 3-roll or 4-roll
        # 3-roll => >= 3 * max_roll * 0.95
        # 4-roll => >= 4 * max_roll * 0.90
        # Otherwise, we do not award that many "full" rolls.
        # We still allow partial, but multi-roll bonus only if it meets threshold.

        # Attempt to see if it meets 4-roll threshold:
        if raw_roll_count >= 3:
            # Only check thresholds if raw_roll_count >=3
            three_roll_min = 3 * max_roll * 0.95
            four_roll_min = 4 * max_roll * 0.90
            
            if value >= four_roll_min:
                # qualifies as a 4-roll
                final_roll_count = raw_roll_count
                multi_rolls_above_2 = 2 # 4-roll => +2
            elif value >= three_roll_min:
                # qualifies as a 3-roll
                final_roll_count = raw_roll_count
                multi_rolls_above_2 = 1 # 3-roll => +1
            else:
                # fails 3-roll threshold => treat as ~2.x
                final_roll_count = raw_roll_count
                multi_rolls_above_2 = 0
        else:
            # < 3 raw rolls => no threshold check
            final_roll_count = raw_roll_count
            multi_rolls_above_2 = 0

        # 3) Add desired stat bonus
        bonus = desired_bonus.get(stat, 0)
        sub_score = final_roll_count + bonus

        # 4) Add multi-roll bonus (if 3+ rolls)
        sub_score += multi_rolls_above_2

        total_score += sub_score

    # --------------------------------------------------------
    # C) Innate Penalty
    # --------------------------------------------------------
    # If 'Innate Stat' is one of the grindable stats => -0.5
    # We'll check if the row has an Innate Stat that is in sub_stats list
    # and if it has a positive value (meaning it exists).
    innate_stat_name = row.get('Innate Stat', '')
    innate_stat_val = row.get('Innate Stat Value', 0)
    if innate_stat_name in stat_list and innate_stat_val > 0:
        # It's presumably a grindable stat => apply penalty
        total_score -= 0.5

    # --------------------------------------------------------
    # D) Slot-Based Modifiers
    # --------------------------------------------------------
    slot_no = int(row.get('slot_no', 0))

    # 1) -2 if slot 2/4/6 is flat main
    main_stat_type = str(row.get('main_stat_type', ''))
    is_flat_main = main_stat_type.upper().startswith('FLAT')
    if slot_no in [2,4,6] and is_flat_main:
        total_score -= 2

    # 2) Additional bonuses for certain main stats
    # Slot 2: +1 if main stat = Speed
    # Slot 4: +1.5 if HP%, +1 if Crit Rate or Crit Dmg
    # Slot 6: +1 if HP% or ATK%
    if slot_no == 2 and main_stat_type.upper() == 'SPD':
        total_score += 1
    elif slot_no == 4:
        if main_stat_type.upper() in ['HP','PERC HP']: # or just 'HP%' if spelled that way
            total_score += 1.5
        elif main_stat_type.upper() in ['CRIT RATE','CR','CRIT Dmg','CRIT DMG']:
            total_score += 1
    elif slot_no == 6:
        if main_stat_type.upper() in ['HP','PERC HP','ATK','PERC ATK']:
            total_score += 1

    # --------------------------------------------------------
    # E) Set-Based Modifier
    # --------------------------------------------------------
    total_score += set_bonus

    return round(total_score, 2)

def get_rolls(runes_df):
    runes_df['New Total Rolls'] = 0
    for stat in stat_list:
        runes_df['New Total Rolls'] = runes_df['New Total Rolls'] + runes_df[stat].fillna(0)/stat_roles[stat]
    return runes_df

def find_reapp_targets(runes_df):
    main_stat_exclude_list = ['Flat HP','Flat Atk','Flat Def','RES','ACC','DEF']

    # limit to legend runes
    mask = runes_df['grade'] == 'legendary'
    filtered_runes = runes_df[mask].copy()
    
    # exclude flats from slots 2,4,6
    mask = ~((filtered_runes['slot_no'].isin([2,4,6])) & (filtered_runes['main_stat_type'].isin(main_stat_exclude_list)))
    filtered_runes = filtered_runes[mask]

    # exclude ATK from slot 4
    mask = ~((filtered_runes['slot_no'] == 4) & (filtered_runes['main_stat_type'] == 'ATK'))
    filtered_runes = filtered_runes[mask]

    # exclude any slot 2 runes that are not SPD
    drop_list = filtered_runes[(filtered_runes['slot_no'] == 2) & (filtered_runes['main_stat_type'] != 'SPD')].index
    filtered_runes = filtered_runes.drop(drop_list)

    # exclude all runes that have and important stat innate (SPD, HP%, DEF%, ATK%)
    mask = ~filtered_runes['Innate Stat'].isin(['SPD','HP','DEF','ATK'])
    filtered_runes = filtered_runes[mask]

    # exclude all runes with 16 or more base speed
    mask = filtered_runes['Base SPD'].fillna(0) < 16
    filtered_runes = filtered_runes[mask]

    # add violent, will runes to the final consideration list
    considered_runes = filtered_runes[filtered_runes['set_id'].isin(['VIOLENT','WILL'])].copy()

    # add violent, slot 2 SPD runes from Swift, Despair to the final consideration list
    mask = (filtered_runes['set_id'].isin(['SWIFT','DESPAIR'])) & (filtered_runes['slot_no'] == 2)
    considered_runes = pd.concat([filtered_runes[mask],considered_runes])
    return considered_runes