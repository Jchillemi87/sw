# %%
import requests
import os
import json
import time
from datetime import datetime, timedelta

import http_utils
from http_utils import get_legacy_session, header

def get_all_monsters():
    """
    Fetches the list of all monsters from the SWARFARM API.
    First checks for a local copy saved as 'monsters_data.json' and returns it if it is not older than 1 month.
    Otherwise, the data is fetched from the API and saved locally.
    
    :return: List of dictionaries containing monster data or an error message.
    """
    file_name = 'monsters_data.json'
    one_month = timedelta(days=30)

    if os.path.exists(file_name):
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_name))
        if datetime.now() - file_mod_time < one_month:
            try:
                with open(file_name, 'r') as f:
                    print("Loading monsters data from local file.")
                    return json.load(f)
            except Exception as e:
                print("Error loading local copy, fetching new data:", e)
    
    base_url = "https://swarfarm.com/api/v2/monsters/"
    monsters = []
    next_url = base_url

    while next_url:
        try:
            response = get_legacy_session().get(next_url, headers=header)
            if response.status_code == 200:
                data = response.json()
                monsters.extend(data['results'])
                next_url = data['next']
            else:
                return {"error": f"Unexpected error: {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {e}"}
    
    try:
        with open(file_name, 'w') as f:
            json.dump(monsters, f)
    except Exception as e:
        print("Error saving data locally:", e)
    
    return monsters

def get_monster_stats(name):
    global all_monsters
    if 'all_monsters' not in globals():
        print('Getting all monster data')
        all_monsters = get_all_monsters()
    monster_data = find_monster_by_name(all_monsters, name)
    if not monster_data:
        return {"error": f"Monster named '{name}' not found."}
    monster_data_dict = {
        'HP': monster_data['base_hp'],
        'ATK': monster_data['base_attack'],
        'DEF': monster_data['base_defense'],
        'SPD': monster_data['speed'],
        'CR': monster_data['crit_rate'],
        'CD': monster_data['crit_damage'],
        'RES': monster_data['resistance'],
        'ACC': monster_data['accuracy']
    }
    return monster_data_dict

def find_monster_by_name(monsters, name):
    """
    Searches for a monster by name in the list of monsters.
    
    :param monsters: List of dictionaries containing monster data.
    :param name: String, name of the monster to search for.
    :return: Dictionary containing the monster's data or None if not found.
    """
    for monster in monsters:
        if monster['name'].lower() == name.lower():
            return monster
    return None

def get_monster_data(monster_id):
    """
    Fetches detailed monster data from SWARFARM API based on the given monster ID.

    :param monster_id: Integer, ID of the monster.
    :return: Dictionary containing monster data or error message.
    """
    base_url = "https://swarfarm.com/api/v2/monsters/"
    url = f"{base_url}{monster_id}/"
    
    try:
        response = get_legacy_session().get(url, headers=header)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return {"error": "Monster not found. Please check the ID."}
        else:
            return {"error": f"Unexpected error: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {e}"}

def get_monster_graphic(monster_id):
    """
    Retrieves the graphic URL for a monster using its detailed data from the SWARFARM API.
    
    :param monster_id: Integer, ID of the monster.
    :return: URL string of the monster's graphic or an error message.
    """
    monster_data = get_monster_data(monster_id)
    if "error" in monster_data:
        return monster_data
    if "image_filename" in monster_data and monster_data["image_filename"]:
        graphic_url = f"https://swarfarm.com/static/herders/images/monsters/{monster_data['image_filename']}"
        return graphic_url
    else:
        return {"error": "Graphic not available for this monster."}

if __name__ == "__main__":
    # Retrieve all monsters
    all_monsters = get_all_monsters()

    if isinstance(all_monsters, list):
        # Search for Rakan
        monster_name = "Rakan"
        rakan_data = find_monster_by_name(all_monsters, monster_name)

        if rakan_data:
            print(f"Found {monster_name}:")
            print(f"ID: {rakan_data['id']}")
            print(f"Element: {rakan_data['element']}")
            print(f"Archetype: {rakan_data['archetype']}")
            
            # Fetch and display full details using the new function
            detailed_rakan_data = get_monster_data(rakan_data['id'])
            print(json.dumps(detailed_rakan_data, indent=4))
            
            # Retrieve and display the monster's graphic URL
            graphic_url = get_monster_graphic(rakan_data['id'])
            if isinstance(graphic_url, dict) and "error" in graphic_url:
                print(graphic_url["error"])
            else:
                print(f"Graphic URL: {graphic_url}")
        else:
            print(f"Monster '{monster_name}' not found.")
    else:
        print(all_monsters)  # Print the error message
# %%