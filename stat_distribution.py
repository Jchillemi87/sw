# %%
import os
import pandas as pd
from datetime import datetime
import importlib

import runes
importlib.reload(runes)
from runes import main_stat_max, impossible_sub_stats, grind, stat_roles

# --- Functions for Loading Data ---

def load_data(file_path):
    """
    Loads CSV data into a pandas DataFrame.
    Attempts several delimiters.
    """
    try:
        df = pd.read_csv(file_path, sep=",")
    except pd.errors.ParserError:
        try:
            df = pd.read_csv(file_path, sep=r'\s+', engine='python')
        except pd.errors.ParserError:
            df = pd.read_csv(file_path, sep=";")
    return df

def load_set_bonuses(file_path):
    """
    Loads set bonus data from a CSV file and returns a dictionary keyed by set name (lowercase).
    Each entry is a dictionary with keys: 'Pieces', 'Stat', and 'Amount'.
    """
    df = pd.read_csv(file_path)
    bonuses = {}
    for _, row in df.iterrows():
        set_name = row["Set"].strip().lower()
        bonuses[set_name] = {
            "Pieces": row["Pieces"],
            "Stat": row["Stat"].strip().upper(),  # uniform stat naming (e.g., HP, ATK, SPD, etc.)
            "Amount": row["Amount"]
        }
    return bonuses

# --- Data Filtering and Grouping ---

def filter_data_by_date(df):
    """
    Filters the DataFrame to include only builds with Data Age on or after January 1 of last year.
    """
    today = datetime.today()
    january_first_last_year = datetime(year=today.year - 1, month=1, day=1)
    df['Data Age'] = pd.to_datetime(df['Data Age'], errors='coerce')
    return df[df['Data Age'] >= january_first_last_year].copy()

def filter_data(df):
    """
    Filters the DataFrame by ordering builds by Score (descending) and Data Age (descending).
    (No sets are excluded.)
    """
    df.sort_values(by=['Score', 'Data Age'], ascending=[False, False], inplace=True)
    return df.copy()

def group_builds_by_set(df):
    """
    Groups builds by the combination of Set1, Set2, and Set3.
    For each group, select the build with the highest Score (most efficient)
    and count how many times that set build appeared.
    Returns a DataFrame with an added 'Build Count' column and a new column 'Set_Build' as a tuple.
    """
    df = df.copy()
    # Create a tuple from the three set columns (order matters here if desired; for order-agnostic, sort the tuple)
    df['Set_Build'] = df.apply(lambda row: (str(row.get("Set1", "")).strip(),
                                            str(row.get("Set2", "")).strip(),
                                            str(row.get("Set3", "")).strip()), axis=1)
    grouped = df.groupby("Set_Build")
    selected_rows = []
    for set_build, group in grouped:
        count = len(group)
        best_build = group.sort_values(by='Score', ascending=False).iloc[0].copy()
        best_build['Build Count'] = count
        selected_rows.append(best_build)
    return pd.DataFrame(selected_rows)

# --- Rune Main Stat Contributions ---

def get_fixed_main_stats():
    """
    Returns fixed main stat contributions for slots 1, 3, and 5.
    Slot 1: Flat HP (2448), Slot 3: Flat ATK (160), Slot 5: Flat DEF (160).
    """
    return {1: ("HP", 2448), 3: ("ATK", 160), 5: ("DEF", 160)}

def get_variable_main_stat_bonus(main_stat, base_stats):
    """
    Given a variable slot’s main stat string, returns its bonus.
    For percentage stats, the bonus is computed as a percentage of the base stat.
    For flat stats, the value is taken directly.
    """
    stat = main_stat.strip().lower()
    if stat == "spd":
        return main_stat_max["SPD"]
    elif stat in ["hp", "%hp"]:
        return base_stats["HP"] * main_stat_max["HP"] / 100.0
    elif stat in ["atk", "%atk"]:
        return base_stats["ATK"] * main_stat_max["ATK"] / 100.0
    elif stat in ["def", "%def"]:
        return base_stats["DEF"] * main_stat_max["DEF"] / 100.0
    elif stat == "cr":
        return main_stat_max["CR"]
    elif stat == "cd":
        return main_stat_max["CD"]
    elif stat == "acc":
        return main_stat_max["ACC"]
    elif stat == "res":
        return main_stat_max["RES"]
    else:
        return 0

# --- Set Bonus Calculation ---

def calculate_set_bonus(build, base_stats, set_bonus_data):
    """
    For a given build, determine the cumulative bonus provided by the equipped sets.
    The build is assumed to have columns 'Set1', 'Set2', 'Set3'.
    
    For each set in the build that exists in set_bonus_data:
      - For percentage stats (HP, ATK, DEF): bonus = base_stats[stat] * (Amount/100)
      - For SPD (SWIFT): bonus = base_stats["SPD"] * (Amount/100)
      - For flat stats (CR, CD, ACC, RES): bonus = Amount
    
    Returns a dictionary with keys for each stat and the total bonus to subtract.
    """
    bonus_totals = {stat: 0 for stat in ["HP", "ATK", "DEF", "SPD", "CR", "CD", "ACC", "RES"]}
    for col in ["Set1", "Set2", "Set3"]:
        set_name = str(build.get(col, "")).strip().lower()
        if set_name in set_bonus_data:
            bonus_info = set_bonus_data[set_name]
            bonus_stat = bonus_info["Stat"]
            amount = bonus_info["Amount"]
            if bonus_stat in ["HP", "ATK", "DEF"]:
                bonus_totals[bonus_stat] += base_stats[bonus_stat] * (amount / 100.0)
            elif bonus_stat == "SPD":
                bonus_totals["SPD"] += base_stats["SPD"] * (amount / 100.0)
            else:
                bonus_totals[bonus_stat] += amount
    return bonus_totals

# --- Eligibility for Substats ---

def available_runes_for_substat(substat, build):
    """
    Returns the count of eligible rune slots (1 to 6) that can contribute the given substat.
    A rune is ineligible if:
      - Its main stat matches the substat.
      - The rune slot is disallowed per the impossible_sub_stats rules.
    """
    count = 0
    fixed = get_fixed_main_stats()
    for slot in range(1, 7):
        if slot in fixed:
            main = fixed[slot][0]
        else:
            main = build.get(f"Slot{slot}", "")
        if main.strip().lower() == substat.strip().lower():
            continue
        if substat in impossible_sub_stats and slot in impossible_sub_stats[substat]:
            continue
        count += 1
    return count

# --- Estimating Substat Rolls per Build ---

def estimate_rolls_for_build(build, base_stats, set_bonus_data):
    """
    For one build (row), estimate the total substat rolls.
    
    For percentage-based stats (HP, ATK, DEF):
      - Compute residual bonus = Final Stat - Base Stat - Fixed contributions - Variable main stat contributions - Set bonuses.
      - Convert the residual to percentage points (dividing by base stat and multiplying by 100).
      - Calculate the average bonus per eligible rune, subtract the legendary grind bonus, and divide by the per-roll value.
    
    For flat stats (SPD, CR, CD, ACC, RES):
      - Compute residual bonus in absolute terms similarly and divide by the per-roll value.
    """
    # Compute initial residual values (absolute) from final stats.
    residual = {stat: build[stat] - base_stats[stat] for stat in ["HP", "ATK", "DEF", "SPD", "CR", "CD", "ACC", "RES"]}
    
    # Subtract fixed main stat contributions (slots 1,3,5).
    fixed = get_fixed_main_stats()
    for slot, (stat_key, value) in fixed.items():
        if stat_key in residual:
            residual[stat_key] -= value

    # Subtract variable main stat contributions (slots 2,4,6).
    for slot in [2, 4, 6]:
        main = build.get(f"Slot{slot}", "")
        bonus = get_variable_main_stat_bonus(main, base_stats)
        m = main.strip().lower()
        if m == "spd":
            residual["SPD"] -= bonus
        elif m in ["hp", "%hp"]:
            residual["HP"] -= bonus
        elif m in ["atk", "%atk"]:
            residual["ATK"] -= bonus
        elif m in ["def", "%def"]:
            residual["DEF"] -= bonus
        elif m == "cr":
            residual["CR"] -= bonus
        elif m == "cd":
            residual["CD"] -= bonus
        elif m == "acc":
            residual["ACC"] -= bonus
        elif m == "res":
            residual["RES"] -= bonus

    # Subtract set bonuses.
    set_bonuses = calculate_set_bonus(build, base_stats, set_bonus_data)
    for stat, bonus in set_bonuses.items():
        residual[stat] -= bonus

    estimated_rolls = {}
    # Process percentage-based stats.
    for stat in ["HP", "ATK", "DEF"]:
        avail = available_runes_for_substat(stat, build)
        if avail <= 0:
            estimated_rolls[stat] = 0
            continue
        bonus_percent = (residual[stat] / base_stats[stat]) * 100
        avg_bonus = bonus_percent / avail
        grind_bonus = grind["legend"].get(stat, 0)
        adjusted_bonus = max(0, avg_bonus - grind_bonus)
        rolls_per_rune = adjusted_bonus / stat_roles[stat]
        total_rolls = rolls_per_rune * avail
        estimated_rolls[stat] = round(total_rolls)

    # Process flat stats.
    for stat in ["SPD", "CR", "CD", "ACC", "RES"]:
        avail = available_runes_for_substat(stat, build)
        if avail <= 0:
            estimated_rolls[stat] = 0
            continue
        avg_bonus = residual[stat] / avail
        grind_bonus = grind["legend"].get(stat, 0) if stat == "SPD" else 0
        adjusted_bonus = max(0, avg_bonus - grind_bonus)
        rolls_per_rune = adjusted_bonus / stat_roles[stat]
        total_rolls = rolls_per_rune * avail
        estimated_rolls[stat] = round(total_rolls)
    
    return estimated_rolls

def analyze_set_builds(df, base_stats, set_bonus_data):
    """
    Processes the filtered builds:
      1. Groups builds by their set combination (Set1, Set2, Set3).
      2. For each group, selects the most efficient build (highest Score) and counts the frequency.
      3. Computes the substat roll distribution for each selected build.
    
    Returns a DataFrame with each set build, its count, and estimated roll distribution,
    and a separate DataFrame with the average distribution across all set builds.
    """
    grouped_df = group_builds_by_set(df)
    results = []
    for _, row in grouped_df.iterrows():
        rolls = estimate_rolls_for_build(row, base_stats, set_bonus_data)
        result = {
            "Set_Build": row['Set_Build'],
            "Build Count": row.get("Build Count", 1),
            "Score": row["Score"]
        }
        result.update(rolls)
        results.append(result)
    results_df = pd.DataFrame(results)
    results_df.sort_values(by="Build Count", ascending=False, inplace=True)
    avg_distribution = results_df[["HP", "ATK", "DEF", "SPD", "CR", "CD", "ACC", "RES"]].mean().round().astype(int)
    avg_distribution_df = pd.DataFrame(avg_distribution).transpose()
    return results_df, avg_distribution_df

# %% --- Main Execution ---

# Monster base stats (Adriana)
# base_stats = {
#     "HP": 10710,
#     "ATK": 736,
#     "DEF": 692,
#     "SPD": 111,
#     "CR": 15,
#     "CD": 50,
#     "ACC": 0,
#     "RES": 15
# }
# player_file = 'adriana_water_vanilla_cookie.csv'

import swarfarm_api
base_stats = swarfarm_api.get_monster_stats('Rakan')

def main():
    current_path = os.path.dirname(os.path.abspath(__file__))
    
    # Load player data.
    file_dir = 'player_data'  # Assumes player_data folder is in the same directory as the script.
    player_file = 'Rakan.csv'
    player_file_path = os.path.join(current_path, file_dir, player_file)
    df = load_data(player_file_path)
    
    # Filter by date (no older than January 1 of last year) and then order by Score and Data Age.
    df_date_filtered = filter_data_by_date(df)
    df_filtered = filter_data(df_date_filtered)
    
    # Load set bonus data.
    set_bonus_file = 'set_bonuses.csv'
    set_bonus_file_path = os.path.join(current_path, set_bonus_file)
    set_bonus_data = load_set_bonuses(set_bonus_file_path)
    
    # Analyze set builds.
    set_builds_df, avg_distribution_df = analyze_set_builds(df_filtered, base_stats, set_bonus_data)
    
    print("Substat Roll Distribution for Each Set Build:")
    print(set_builds_df)
    print("\nAverage Substat Roll Distribution Across All Set Builds:")
    print(avg_distribution_df)

if __name__ == "__main__":
    main()
# %%