# %%
import requests
import json

def get_all_monsters():
    """
    Fetches the list of all monsters from the SWARFARM API.
    :return: List of dictionaries containing monster data or an error message.
    """
    base_url = "https://swarfarm.com/api/v2/monsters/"
    monsters = []
    next_url = base_url

    while next_url:
        try:
            response = requests.get(next_url)
            if response.status_code == 200:
                data = response.json()
                monsters.extend(data['results'])
                next_url = data['next']
            else:
                return {"error": f"Unexpected error: {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {e}"}

    return monsters

def get_monster_stats(name):
    global all_monsters
    if 'all_monsters' not in globals():
        print('Getting all monster data')
        all_monsters = get_all_monsters()
    monster_data = find_monster_by_name(all_monsters,name)
    monster_data_dict = {
        'HP':monster_data['base_hp']
        ,'ATK':monster_data['base_attack']
        ,'DEF':monster_data['base_defense']
        ,'SPD':monster_data['speed']
        ,'CR':monster_data['crit_rate']
        ,'CD':monster_data['crit_damage']
        ,'RES':monster_data['resistance']
        ,'ACC':monster_data['accuracy']
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

    :param monster_id: Integer, ID of the monster
    :return: Dictionary containing monster data or error message
    """
    base_url = "https://swarfarm.com/api/v2/monsters/"
    url = f"{base_url}{monster_id}/"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()  # Return JSON response
        elif response.status_code == 404:
            return {"error": "Monster not found. Please check the ID."}
        else:
            return {"error": f"Unexpected error: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {e}"}
# %%
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
        else:
            print(f"Monster '{monster_name}' not found.")
    else:
        print(all_monsters)  # Print the error message

# %%
