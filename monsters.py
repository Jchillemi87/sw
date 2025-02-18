# %%
import os
import pandas as pd
import stat_distribution
from stat_distribution import (
    load_data,
    load_set_bonuses,
    filter_data_by_date,
    filter_data,
    analyze_set_builds,
    base_stats
)

# Import SWARFARM API functions
import swarfarm_api as sa

def get_monster_player_data(monster_name, base_dir='player_data'):
    """
    Constructs a filename based on the monster name (e.g., 'rakan.csv')
    and loads the player data.
    """
    # Check if the monster name has an alternate name in the dictionary
    monster_name = monster_file_names.get(monster_name, monster_name)
    
    # Adjust the filename format as needed.
    filename = f"{monster_name.lower()}.csv"
    file_path = os.path.join(base_dir, filename)
    if not os.path.exists(file_path):
        print(f"Player data file for {monster_name} not found at: {file_path}")
    return load_data(file_path)

def analyze_monster(monster_name):
    """
    Given a monster name, fetch monster details from the SWARFARM API, load its player data,
    and run the substat roll distribution analysis.
    """
    print(f"=== Analyzing {monster_name} ===")
    
    # Get monster list from SWARFARM and search for the monster.
    monster_data = sa.find_monster_by_name(all_monsters, monster_name)
    if not monster_data:
        print(f"Monster {monster_name} not found in SWARFARM API data.")
    else:
        print("Monster Details:")
        print(f"  ID: {monster_data['id']}")
        print(f"  Element: {monster_data.get('element', 'N/A')}")
        print(f"  Archetype: {monster_data.get('archetype', 'N/A')}")
    
    # Load the player data CSV for the monster.
    df = get_monster_player_data(monster_name)
    
    # Filter builds by date (no older than January 1 of last year) and order by Score and Data Age.
    df_date_filtered = filter_data_by_date(df)
    df_filtered = filter_data(df_date_filtered)
    
    # Load set bonus data (assumed to be in the same directory as the script).
    current_path = os.path.dirname(os.path.abspath(__file__))
    set_bonus_file = 'set_bonuses.csv'
    set_bonus_file_path = os.path.join(current_path, set_bonus_file)
    set_bonus_data = load_set_bonuses(set_bonus_file_path)
    
    # Run analysis: group builds by set, select the best build per set, compute substat roll distribution.
    set_builds_df, avg_distribution_df = analyze_set_builds(df_filtered, base_stats, set_bonus_data)
    
    print("\nSubstat Roll Distribution for Each Set Build:")
    print(set_builds_df)
    print("\nAverage Substat Roll Distribution Across All Set Builds:")
    print(avg_distribution_df)
    print("=" * 60 + "\n")

def load_my_monsters(data):
    """
    Loads the player's monster data and maps monster IDs to names using SWARFARM API.
    """
    my_monsters = pd.DataFrame.from_dict(data['unit_list'])
    
    # Fetch all monsters from SWARFARM API
    all_monsters = sa.get_all_monsters()
    
    # Create a mapping from unit_master_id to name
    monster_id_to_name = {monster['com2us_id']: monster['name'].lower() for monster in all_monsters}
    
    # Map names using the dictionary
    my_monsters['name'] = my_monsters['unit_master_id'].map(monster_id_to_name).str.lower()
    
    # Load additional monster summaries
    monster_summaries = pd.read_csv('monster_summaries.csv')
    
    element_list = ['water', 'fire', 'wind', 'light', 'dark']
    
    monster_summaries = monster_summaries.dropna(subset=['name'])
    
    index_of_missing_site_names = monster_summaries[
        monster_summaries['site_name'].isna() & ~monster_summaries['name'].isna()
    ].index
    
    monster_summaries.loc[index_of_missing_site_names, 'name'] = (
        monster_summaries.loc[index_of_missing_site_names, 'name']
        .str.replace(r'(_' + '|_'.join(element_list) + r').*', '', regex=True)
    )
    monster_summaries.loc[index_of_missing_site_names, 'site_name'] = (
        monster_summaries.loc[index_of_missing_site_names, 'name']
        .str.replace(r'(_' + '|_'.join(element_list) + r').*', '', regex=True)
    )
    
    # Process missing names
    my_monsters = my_monsters.dropna(subset=['name'])
    my_monsters['missing_summary'] = ~my_monsters['name'].isin(monster_summaries['name'])
    my_monsters['fixed_name'] = my_monsters['name']
    my_monsters.loc[my_monsters['missing_summary'], 'fixed_name'] = (
        my_monsters.loc[my_monsters['missing_summary'], 'name']
        .apply(lambda name: find_missing_name(name, monster_summaries))
    )
    
    my_monsters = my_monsters.set_index('fixed_name').join(monster_summaries.set_index('name'), how='left')
    my_monsters.reset_index(drop=True, inplace=True)
    
    return my_monsters

def find_missing_name(name, df):
    import re
    if pd.isna(name):
        return ''
    name = name.replace(' ', '_')
    df = df.dropna(subset=['name'])
    match = df[df['name'].str.contains(re.escape(name), case=False, na=False)]
    return '' if len(match) == 0 else match['name'].values[0]


monster_file_names = {
    'Adriana': 'adriana_water_vanilla_cookie',
    'Ahmed': 'ahmed_light_bayek',
    'Alice': 'alice_fire_hollyberry_cookie',
    'Angela': 'angela_wind_vanilla_cookie',
    'Ariana': 'ariana_light_vanilla_cookie',
    'Ashour': 'ashour_fire_bayek',
    'Audrey': 'audrey_light_hollyberry_cookie',
    'Aurelia': 'aurelia_light_kassandra',
    'Berenice': 'berenice_fire_chun_li',
    'Berghild': 'berghild_light_eivor',
    'Bernadotte': 'bernadotte_fire_ken',
    'Borgnine': 'borgnine_water_m_bison',
    'Cayde': 'cayde_dark_dhalsim',
    'Cordelia': 'cordelia_wind_chun_li',
    'Craig': 'craig_light_m_bison',
    'Douglas': 'douglas_fire_ryu',
    'Elana': 'elana_dark_vanilla_cookie',
    'Eleni': 'eleni_wind_kassandra',
    'Federica': 'federica_fire_kassandra',
    'Frederic': 'frederic_light_altair',
    'Fudge': 'fudge_light_madeleine_cookie',
    'Ganache': 'ganache_water_madeleine_cookie',
    'Giselle': 'giselle_dark_hollyberry_cookie',
    'Hector': 'hector_wind_ezio',
    'Hekerson': 'hekerson_light_dhalsim',
    'Hibiscus': 'hibiscus_fire_espresso_cookie',
    'Ian': 'ian_light_ezio',
    'Jade': 'jade_wind_hollyberry_cookie',
    'Jarrett': 'jarrett_wind_dhalsim',
    'Jasmine': 'jasmine_light_espresso_cookie',
    'Kalantatze': 'kalantatze_water_kassandra',
    'Karnal': 'karnal_fire_m_bison',
    'Kashmir': 'kashmir_wind_ryu',
    'Kiara': 'kiara_dark_kassandra',
    'Kyle': 'kyle_water_dhalsim',
    'Lariel': 'lariel_water_chun_li',
    'Lavender': 'lavender_dark_espresso_cookie',
    'Leah': 'leah_light_chun_li',
    'Light Ciri': 'light_ciri',
    'Light Triss': 'light_triss',
    'Light Yennefer': 'light_yennefer',
    'Lionel': 'lionel_water_ezio',
    'Lucia': 'lucia_fire_vanilla_cookie',
    'Manon': 'manon_water_hollyberry_cookie',
    'Moore': 'moore_water_ryu',
    'Patrick': 'patrick_fire_ezio',
    'Pavé': 'pavé_fire_madeleine_cookie',
    'Praline': 'praline_wind_madeleine_cookie',
    'Rosemary': 'rosemary_water_espresso_cookie',
    'Sagar': 'sagar_wind_m_bison',
    'Salah': 'salah_dark_bayek',
    'Shahat': 'shahat_wind_bayek',
    'Solveig': 'solveig_fire_eivor',
    'Sigrid': 'sigrid_dark_eivor',
    'Talisman': 'talisman_light_ryu',
    'Truffle': 'truffle_dark_madeleine_cookie',
    'Vancliffe': 'vancliffe_dark_ryu',
    'Vareesa': 'vereesa_dark_chun_li',
    'Water Ciri': 'water_ciri',
    'Water Geralt': 'water_geralt',
    'Wind Ciri': 'wind_ciri',
    'Wind Geralt': 'wind_geralt'
}

# %%
def main():
    # Example monsters: Rakan and Leah
    monsters_to_analyze = ['Giselle','Adriana','Leah','Rakan']
    for monster in monsters_to_analyze:
        analyze_monster(monster)

if __name__ == "__main__":
    all_monsters = sa.get_all_monsters()
    main()
# %%