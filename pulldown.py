# %%
from io import StringIO
import pandas as pd
import requests
import re

import http_utils
from http_utils import get_legacy_session, header
 
# %%
# Stat constants
stat_columns = ['HP', 'ATK', 'DEF', 'SPD', 'CR', 'CD', 'RES', 'ACC']
stat_roll = {'hp': 8, 'atk': 8, 'def': 8, 'spd': 8, 'cr': 6, 'cd': 7, 'res': 8, 'acc': 8}
all_main_stats = {'hp+': 2448, 'hp%': 63, 'atk+': 160, 'atk%': 63, 'def+': 160, 'def%': 63, 'spd': 42, 'cr': 58, 'cd': 80, 'acc': 64, 'res': 64}
main_stats = {'HP': 63, 'ATK': 63, 'DEF': 63, 'SPD': 42, 'CR': 58, 'CD': 80, 'ACC': 64, 'RES': 64}
max_stats_from_runes_dic = {
    'HP': 3.39,
    'ATK': 3.39,
    'DEF': 3.39,
    'SPD': 217,
    'CR': 100,
    'CD': 255,
    'RES': 100,
    'ACC': 85
}

# %%
# Helper functions for canonical names

def canonical_monster_url(name: str) -> str:
    """
    Convert a monster name from the scraped list (for example, 
    "Sagar / Wind M. Bison") into the correct URL slug:
      - Lower-case, trimmed,
      - The slash (" / ") is replaced with an underscore,
      - Spaces are replaced with underscores,
      - Periods are removed and hyphens are converted to underscores.
    
    Example:
      "Sagar / Wind M. Bison" -> "sagar_wind_m_bison"
    """
    s = name.lower().strip()
    s = s.replace(" / ", "_")
    s = s.replace(" ", "_")
    s = s.replace(".", "")    # Remove dots (e.g., "M. Bison" -> "m_bison")
    s = s.replace("-", "_")    # Convert dashes to underscores (e.g., "Chun-Li" -> "chun_li")
    return s

def canonical_file_name(name: str) -> str:
    """
    Use only the base Summoners War name for file saving.
    For example, "Sagar / Wind M. Bison" returns "sagar".
    For non-collab names (without " / ") the full name is used (with spaces replaced by underscores).
    """
    if " / " in name:
        base = name.split(" / ")[0]
    else:
        base = name
    return base.lower().strip().replace(" ", "_")

# %%
def get_html_text(monster='Vigor'):
    # Build URL using the canonical URL name.
    url_name = canonical_monster_url(monster)
    url = f'https://godsarmy.garude.de/monsters/{url_name}'

    # Special-case for Feng Yan:
    missing_monster_dic = {'feng_yan': 'https://godsarmy.garude.de/node/228'}
    if url_name in missing_monster_dic:
        url = missing_monster_dic[url_name]
    
    try:
        r = get_legacy_session().get(url, headers=header)
        if r.status_code == 200:
            html_text = re.sub('<img title="', '', r.text)
            html_text = re.sub('" src="https://godsarmy.garude.de/sites/default/files/.*?.png">', '', html_text)
            return html_text
        else:
            return None
    except requests.RequestException as e:
        print(f"Failed to retrieve data for {monster}: {str(e)}")
        return None
 
def get_player_data(html_text=None, newest=True):
    if html_text is None:
        print("No HTML text provided or failed to load HTML text.")
        return None

    try:
        tables = pd.read_html(StringIO(html_text))
        if len(tables) < 3:
            print(f"Expected at least 3 tables but found only {len(tables)}.")
            return None
        elif len(tables) == 3:
            # For pages that only have 3 tables, use table 2 as player data.
            player_data = tables[2]
        else:
            # If there are 4 or more tables, combine tables 2 and 3.
            player_data = pd.concat([tables[2], tables[3]], axis=0, ignore_index=True)
    except ValueError as e:
        print(f"Error processing HTML tables: {str(e)}")
        return None

    reDic = {r'(.|\n)*\(': '', r'\).*': ''}
    player_data = player_data.replace(reDic, regex=True).drop(columns='Calc')

    # Process the 'Sets' column
    player_data['Sets'] = player_data['Sets'].fillna('Unknown')
    sets_data = player_data['Sets'].str.upper().str.split(r'\s').apply(lambda x: x + ['Unknown'] * (3 - len(x)))
    set_df = pd.DataFrame(sets_data.tolist(), columns=['Set1', 'Set2', 'Set3'])
    player_data = pd.concat([player_data, set_df], axis=1)

    # Process the 'Slots' column
    player_data['Slots'] = player_data['Slots'].fillna('Unknown SPD Unknown')
    slots_data = player_data['Slots'].str.upper().str.split(r'\s').apply(lambda x: x + ['Unknown'] * (3 - len(x)))
    slots_df = pd.DataFrame(slots_data.tolist(), columns=['Slot2', 'Slot4', 'Slot6'])
    player_data = pd.concat([player_data, slots_df], axis=1)

    # Convert stat columns to integers
    for stat in ['HP', 'ATK', 'DEF', 'SPD']:
        player_data[stat] = player_data[stat].str.replace('.', '', regex=False).str.strip().astype(int)
    player_data[['HP', 'ATK', 'DEF', 'SPD', 'CR', 'CD', 'ACC', 'RES']] = player_data[['HP', 'ATK', 'DEF', 'SPD', 'CR', 'CD', 'ACC', 'RES']].astype(int)
    
    # Convert 'Data Age' to datetime; replace blanks with a very old date.
    player_data['Data Age'] = pd.to_datetime(player_data['Data Age'], format='%d.%m.%Y', errors='coerce')
    player_data['Data Age'] = player_data['Data Age'].fillna(pd.to_datetime('1900-01-01'))

    if newest:
        year = pd.to_datetime('today').year - 1
        newest_data = player_data[player_data['Data Age'].dt.year >= year]
        if newest_data.shape[0] >= 5:
            player_data = newest_data
        else:
            player_data = player_data.sort_values(by='Data Age', ascending=False).head(10)

    player_data = player_data.drop_duplicates()
    return player_data
 
def get_base_stats(html_text):
    base_stats = pd.read_html(StringIO(html_text))[0]
    base_stats['HP'] *= 1000
    base_stats['HP'] = base_stats['HP'].astype(int)
    return base_stats
 
def get_rune_main_stat(df, base_stats):
    df[['slot2_value', 'slot4_value', 'slot6_value']] = df[['Slot2', 'Slot4', 'Slot6']].replace({'Slot2': main_stats, 'Slot4': main_stats, 'Slot6': main_stats})
    slot2Pivot = df.pivot(columns=['Slot2'], values='slot2_value')
    slot4Pivot = df.pivot(columns=['Slot4'], values='slot4_value')
    slot6Pivot = df.pivot(columns=['Slot6'], values='slot6_value')
    slotsPivot = pd.DataFrame(columns=main_stats.keys())
    slotsPivot = pd.concat([slotsPivot, slot2Pivot, slot4Pivot, slot6Pivot], axis=1)
    slotsPivot = slotsPivot.T.groupby(level=0).sum().T
    slotsPivot = slotsPivot[stat_columns].astype(int)
    slotsPivot[['HP', 'ATK', 'DEF']] = slotsPivot[['HP', 'ATK', 'DEF']].apply(lambda x: 1 + (x/100))
    slotsPivot[['HP', 'ATK', 'DEF']] = slotsPivot[['HP', 'ATK', 'DEF']].multiply(base_stats.loc[0, ['HP', 'ATK', 'DEF']])
    return
 
def get_max_stats(base_stats):
    max_stats = {'HP': 0,
                 'ATK': 0,
                 'DEF': 0,
                 'SPD': 217,
                 'CR': 100,
                 'CD': 255,
                 'RES': 100,
                 'ACC': 85}
    max_stats['HP'] = base_stats['HP'] * (1 + max_stats_from_runes_dic['HP'])
    max_stats['ATK'] = base_stats['ATK'] * (1 + max_stats_from_runes_dic['ATK'])
    max_stats['DEF'] = base_stats['DEF'] * (1 + max_stats_from_runes_dic['DEF'])
    max_stats['SPD'] = int(base_stats['SPD'].iloc[0]) + int(max_stats_from_runes_dic['SPD'])
    max_stats['CR'] = max_stats_from_runes_dic['CR']
    max_stats['CD'] = max_stats_from_runes_dic['CD']
    max_stats['RES'] = max_stats_from_runes_dic['RES']
    max_stats['ACC'] = max_stats_from_runes_dic['ACC']
 
    max_stats['HP'] = int(max_stats['HP'].iloc[0])
    max_stats['ATK'] = int(max_stats['ATK'].iloc[0])
    max_stats['DEF'] = int(max_stats['DEF'].iloc[0])
    max_stats['SPD'] = int(max_stats['SPD'])
    return pd.DataFrame(max_stats, index=[0])

def get_monster_summary(monster_name: str) -> dict:
    print('Checking monster:', monster_name)
    html_text = get_html_text(monster_name)
    if html_text is None:
        return {"error": f"No data available for {monster_name}. Unable to retrieve or parse HTML.",
                "name": monster_name,
                "site_name": monster_name}

    player_data = get_player_data(html_text)
    if player_data is None:
        return {"error": f"Failed to process player data for {monster_name}.",
                "name": monster_name,
                "site_name": monster_name}

    # Save player data using the canonical file name.
    file_name = canonical_file_name(monster_name)
    player_data.to_csv('player_data/' + file_name + '.csv', index=False)
    
    base_stats = get_base_stats(html_text)
    if base_stats is None:
        return {"error": f"Failed to retrieve base stats for {monster_name}.",
                "name": monster_name,
                "site_name": monster_name}

    # Optionally, calculate rune main stats.
    # runeMainStats = get_rune_main_stat(player_data, base_stats)
    max_stats = get_max_stats(base_stats)
    
    sets_used = player_data.groupby(['Set1', 'Set2'], dropna=False).size().sort_values(ascending=False).reset_index(name='count')
    main_slots_used = player_data.groupby(['Slot2', 'Slot4', 'Slot6'], dropna=False).size().sort_values(ascending=False).reset_index(name='count')
    
    main_sets = sets_used.groupby('Set1').sum(numeric_only=True).sort_values(['count'], ascending=False)
    offset_sets = sets_used.groupby('Set2').sum(numeric_only=True).sort_values(['count'], ascending=False)

    # Remove base stats from player_data
    for stat in base_stats.columns[:8]:
        player_data[stat] = player_data[stat] - base_stats[stat].iloc[0]

    # Remove stats from slots 1, 3, and 5
    player_data['HP'] -= all_main_stats['hp+']
    player_data['DEF'] -= all_main_stats['def+']
    player_data['ATK'] -= all_main_stats['atk+']

    def remove_main_slot_stats(row):
        perc_main_stats = ['HP', 'ATK', 'DEF']
        other_main_stats = ['SPD', 'CR', 'CD', 'RES', 'ACC']
        for main_slot in ['Slot2', 'Slot4', 'Slot6']:
            stat = row[main_slot]
            if stat in perc_main_stats:
                stat_perc = base_stats[stat].iloc[0] * (main_stats[stat] / 100)
                row[stat] = row[stat] - stat_perc
            elif stat in other_main_stats:
                row[stat] = row[stat] - main_stats[stat]
        return row
    
    player_data = player_data.apply(remove_main_slot_stats, axis=1)
    stat_focus_percent = player_data[['HP', 'ATK', 'DEF', 'SPD', 'CR', 'CD', 'RES', 'ACC']].divide(max_stats.loc[0, list(main_stats.keys())])
    stat_rank = stat_focus_percent.rank(axis=1, method='min', ascending=False).mean().sort_values(ascending=True)

    slot2s = main_slots_used.groupby('Slot2').sum(numeric_only=True).sort_values(['count'], ascending=False)
    slot4s = main_slots_used.groupby('Slot4').sum(numeric_only=True).sort_values(['count'], ascending=False)
    slot6s = main_slots_used.groupby('Slot6').sum(numeric_only=True).sort_values(['count'], ascending=False)

    def format_stat_rank(rank_series):
        return ' > '.join(rank_series.index)

    stat_efficiency_multiplier = pd.DataFrame()
    stat_efficiency_multiplier['rank'] = stat_rank
    stat_efficiency_multiplier['rank_div'] = stat_efficiency_multiplier['rank'].shift(-1).div(stat_efficiency_multiplier['rank']).fillna(1)
    stat_efficiency_multiplier['efficiency_multiplier'] = stat_efficiency_multiplier['rank_div'][::-1].cumprod()[::-1]

    summary = {
        'name': monster_name,
        'site_name': monster_name,
        'most_popular_mainset': main_sets.index[0] if not main_sets.empty else None,
        'most_popular_offset': offset_sets.index[0] if not offset_sets.empty else None,
        'most_popular_slot2': slot2s.index[0] if not slot2s.empty else None,
        'most_popular_slot4': slot4s.index[0] if not slot4s.empty else None,
        'most_popular_slot6': slot6s.index[0] if not slot6s.empty else None,
        'stats_priority': format_stat_rank(stat_rank),
        'main_sets': format_stat_rank(main_sets) if not main_sets.empty else None,
        'offset_sets': format_stat_rank(offset_sets) if not offset_sets.empty else None,
        'slot2s': format_stat_rank(slot2s) if not slot2s.empty else None,
        'slot4s': format_stat_rank(slot4s) if not slot4s.empty else None,
        'slot6s': format_stat_rank(slot6s) if not slot6s.empty else None,
        'HP_value': round(stat_efficiency_multiplier['efficiency_multiplier'].get('HP', 0), 2) if 'HP' in stat_efficiency_multiplier['efficiency_multiplier'] else 0,
        'ATK_value': round(stat_efficiency_multiplier['efficiency_multiplier'].get('ATK', 0), 2) if 'ATK' in stat_efficiency_multiplier['efficiency_multiplier'] else 0,
        'DEF_value': round(stat_efficiency_multiplier['efficiency_multiplier'].get('DEF', 0), 2) if 'DEF' in stat_efficiency_multiplier['efficiency_multiplier'] else 0,
        'SPD_value': round(stat_efficiency_multiplier['efficiency_multiplier'].get('SPD', 0), 2) if 'SPD' in stat_efficiency_multiplier['efficiency_multiplier'] else 0,
        'CR_value': round(stat_efficiency_multiplier['efficiency_multiplier'].get('CR', 0), 2) if 'CR' in stat_efficiency_multiplier['efficiency_multiplier'] else 0,
        'CD_value': round(stat_efficiency_multiplier['efficiency_multiplier'].get('CD', 0), 2) if 'CD' in stat_efficiency_multiplier['efficiency_multiplier'] else 0,
        'ACC_value': round(stat_efficiency_multiplier['efficiency_multiplier'].get('ACC', 0), 2) if 'ACC' in stat_efficiency_multiplier['efficiency_multiplier'] else 0,
        'RES_value': round(stat_efficiency_multiplier['efficiency_multiplier'].get('RES', 0), 2) if 'RES' in stat_efficiency_multiplier['efficiency_multiplier'] else 0
    }
    return summary
 
# %%
def get_monster_list():
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    monster_list = pd.DataFrame()
    for letter in alphabet:
        try:
            r = get_legacy_session().get('https://godsarmy.garude.de/monsters/' + letter, headers=header)
        except Exception as e:
            print('Error:', letter, e)
            continue
        html_text = re.sub('<img title="', '', r.text)
        html_text = re.sub('" src=https://godsarmy.garude.de/sites/default/files/.*?.png>', '', html_text)
        try:
            current_table = pd.read_html(StringIO(html_text))[0]
        except Exception as e:
            print('Error reading table for letter', letter, e)
            continue
        monster_list = pd.concat([monster_list, current_table], axis=0)
        icon_base_url = 'https://godsarmy.garude.de/sites/default/files/styles/thumbnail/public/monster_icons/'
        # Use our canonical URL function for icon names if desired.
        monster_list['monster_icon_name'] = monster_list['Name'].apply(lambda n: canonical_monster_url(n))
        monster_list['monster_icon_link'] = icon_base_url + monster_list['monster_icon_name'] + '_100x100.png'
    return monster_list

def get_first_n_stats(line, n=4):
    if not isinstance(line, str):
        return None
    stats = line.split('>')
    first_n = stats[:n]
    return '>'.join(first_n).strip()
 
# %%
if __name__ == '__main__':
    monster_list = get_monster_list()
    if not monster_list.empty:
        # For each monster, use its original Name from the list.
        monster_summaries = monster_list.apply(lambda x: get_monster_summary(x['Name']), axis=1)
        valid_summaries = [summary for summary in monster_summaries if summary is not None]
        monster_summaries_df = pd.DataFrame(valid_summaries)

        # Add columns for the top 2, 3, and 4 sub-stats
        monster_summaries_df['top_2_sub_stats'] = monster_summaries_df['stats_priority'].apply(lambda x: get_first_n_stats(x, n=2))
        monster_summaries_df['top_3_sub_stats'] = monster_summaries_df['stats_priority'].apply(lambda x: get_first_n_stats(x, n=3))
        monster_summaries_df['top_4_sub_stats'] = monster_summaries_df['stats_priority'].apply(lambda x: get_first_n_stats(x, n=4))

        if not monster_summaries_df.empty:
            monster_summaries_df.to_csv('monster_summaries.csv', index=False)
        else:
            print("No valid monster data was processed.")
    else:
        print("No monster data available to process.")
# %%
