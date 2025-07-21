import os
import requests
import time
import pandas as pd
from dotenv import load_dotenv
from collections import Counter, defaultdict
from itertools import combinations

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
MASS_REGION = "americas"
TFT_SET = 14  # Set number for filtering matches

def get_match_ids(puuid):
    if not API_KEY:
        raise Exception("RIOT_API_KEY not found in environment variables")
    
    url = f"https://{MASS_REGION}.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids?start=0&count=50&api_key={API_KEY}"
    print(f"Requesting match IDs for PUUID: {puuid[:8]}...")
    
    try:
        resp = requests.get(url, timeout=15)
        print(f"Match IDs response: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"Found {len(data)} matches")
            return data
        elif resp.status_code == 401:
            raise Exception("Invalid API key - check RIOT_API_KEY environment variable")
        elif resp.status_code == 404:
            raise Exception("PUUID not found or no matches available")
        elif resp.status_code == 429:
            print("Rate limited on match IDs request, waiting...")
            time.sleep(15)
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                return resp.json()
            else:
                raise Exception("Rate limited - please try again in a few minutes")
        else:
            raise Exception(f"API error: {resp.status_code}")
        
    except requests.exceptions.Timeout:
        raise Exception("Request timed out - API may be slow, try again")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error: {str(e)}")

def get_match_data(match_id):
    url = f"https://{MASS_REGION}.api.riotgames.com/tft/match/v1/matches/{match_id}?api_key={API_KEY}"
    max_retries = 2
    
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, timeout=20)
            
            if resp.status_code == 200:
                data = resp.json()
                if 'info' not in data or 'participants' not in data.get('info', {}):
                    print(f"Match {match_id}: Invalid structure")
                    return None
                
                return data
            elif resp.status_code == 429:
                wait_time = 10
                print(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            elif resp.status_code == 404:
                print(f"Match {match_id}: Not found")
                return None
            else:
                print(f"Match {match_id}: Error {resp.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"Match {match_id}: Timeout")
            if attempt < max_retries - 1:
                time.sleep(3)
        except Exception as e:
            print(f"Match {match_id}: Exception {str(e)}")
            return None
    
    return None

def get_unit_traits_from_data(unit_name, cd_data):
    """Get native traits of a unit from Community Dragon data"""
    def find_unit(obj):
        if isinstance(obj, dict):
            if obj.get("apiName") == unit_name and "traits" in obj:
                return obj["traits"]
            for v in obj.values():
                result = find_unit(v)
                if result:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = find_unit(item)
                if result:
                    return result
        return []
    
    return find_unit(cd_data)

def analyze_unit(unit_df, unit_name, cd_data, top_n=10, min_games=3):
    """Analyze a specific unit's performance with different item combinations and traits"""
    df = unit_df[unit_df['unit'] == unit_name].copy()
    print(f"Analyzing Unit: {unit_name}")
    print(f"Total Games Found: {len(df)}")
    
    if len(df) < min_games:
        print(f"Not enough games to analyze (min required: {min_games})")
        return {
            'error': f'Not enough games for {unit_name} (found {len(df)}, need {min_games})',
            'unit_name': unit_name,
            'games_found': len(df)
        }

    # ---- Item Combinations (1-3 item sets) ----
    item_combo_rows = []
    for _, row in df.iterrows():
        items = [i for i in [row['item_1'], row['item_2'], row['item_3']] if i]
        for r in range(1, len(items) + 1):
            for combo in combinations(sorted(items), r):
                item_combo_rows.append({
                    'items': ' | '.join(combo),
                    'placement': row['placement']
                })

    item_combo_df = pd.DataFrame(item_combo_rows)
    if len(item_combo_df) > 0:
        item_stats = (
            item_combo_df.groupby('items')['placement']
            .agg(['mean', 'count'])
            .reset_index()
        )
        
        # Filter: only show combos seen in at least 3 games
        item_stats = item_stats[item_stats['count'] >= 3]
        
        # Sort and take top N
        item_stats = item_stats.sort_values('mean').head(top_n).reset_index(drop=True)
        
        # Convert to list of dicts for JSON response
        top_item_combos = []
        for _, row in item_stats.iterrows():
            top_item_combos.append({
                'items': row['items'],
                'avg_placement': round(row['mean'], 2),
                'games': int(row['count'])
            })
    else:
        top_item_combos = []

    # ---- Trait Performance (filtering out native traits) ----
    df_exploded = df.explode('traits')
    
    # Normalize trait names by removing 'TFT14_'
    df_exploded['traits'] = df_exploded['traits'].str.replace('TFT14_', '')
    
    # Get native traits and exclude them
    native_traits = get_unit_traits_from_data(unit_name, cd_data)
    df_exploded = df_exploded[~df_exploded['traits'].isin(native_traits)]
    
    if len(df_exploded) > 0:
        trait_stats = (
            df_exploded.groupby('traits')['placement']
            .agg(['mean', 'count'])
            .reset_index()
            .sort_values('mean')
            .head(top_n)
            .reset_index(drop=True)
        )
        
        # Convert to list of dicts for JSON response
        top_traits = []
        for _, row in trait_stats.iterrows():
            top_traits.append({
                'trait': row['traits'],
                'avg_placement': round(row['mean'], 2),
                'games': int(row['count'])
            })
    else:
        top_traits = []

    return {
        'unit_name': unit_name,
        'games_analyzed': len(df),
        'item_combinations': top_item_combos,
        'synergy_traits': top_traits,
        'native_traits': native_traits
    }

def run_analysis(puuid, unit_name=None):
    """Run units analysis for a player"""
    try:
        print(f"Starting units analysis for PUUID: {puuid[:8]} (TFT Set {TFT_SET})...")
        
        # Get match IDs
        match_ids = get_match_ids(puuid)
        if not match_ids:
            raise Exception("No match IDs found")
        
        print(f"Processing {len(match_ids)} matches...")
        
        # Data structure for units analysis
        data = {
            'set_number': [],
            'placement': [],
            'level': [],
            'traits': [],
            'units': [],
            'items': []
        }
        successful_matches = 0
        
        for i, match_id in enumerate(match_ids):
            if i > 0 and i % 10 == 0:
                print(f"Processed {i} matches, brief pause...")
                time.sleep(3)
            
            match_data = get_match_data(match_id)
            if not match_data:
                continue
            
            try:
                set_number = match_data['info']['tft_set_number']
                data['set_number'].append(set_number)
                
                index = None
                for pos, participant_puuid in enumerate(match_data['metadata']['participants']):
                    if puuid == participant_puuid:
                        index = pos
                        break
                
                if index is None:
                    print(f"Player not found in match {match_id}")
                    data['set_number'].pop()
                    continue
                
                participant_data = match_data['info']['participants'][index]
                
                placement = participant_data['placement']
                level = participant_data['level']
                traits = [trait['name'] for trait in participant_data['traits']]
                units = [unit['character_id'] for unit in participant_data['units']]
                items = [item.get('itemNames', []) for item in participant_data['units']]
                
                data['placement'].append(placement)
                data['level'].append(level)
                data['traits'].append(traits)
                data['units'].append(units)
                data['items'].append(items)
                
                successful_matches += 1
                
            except Exception as e:
                print(f"Error processing match {match_id}: {str(e)}")
                if len(data['set_number']) > len(data['placement']):
                    data['set_number'].pop()
                continue
        
        if successful_matches < 3:
            raise Exception(f"Insufficient data - only {successful_matches} valid matches found")
        
        print(f"Successfully processed {successful_matches} matches")
        
        # Create DataFrame and filter by set
        df = pd.DataFrame(data)
        df = df[df['set_number'] == TFT_SET].copy()
        
        if len(df) < 3:
            raise Exception(f"Insufficient Set {TFT_SET} data - only {len(df)} matches from Set {TFT_SET}")
        
        print(f"Found {len(df)} Set {TFT_SET} matches")
        
        # Create unit rows for analysis (similar to your original code)
        unit_rows = []
        for _, row in df.iterrows():
            active_traits = row['traits']
            placement = row['placement']
            units = row['units']
            items_per_unit = row['items']

            for unit_name_iter, item_list in zip(units, items_per_unit):
                # Pad/truncate item list to 3
                item_list = item_list[:3] + [None] * (3 - len(item_list))
                unit_rows.append({
                    'unit': unit_name_iter,
                    'item_1': item_list[0],
                    'item_2': item_list[1],
                    'item_3': item_list[2],
                    'placement': placement,
                    'traits': active_traits
                })

        unit_df = pd.DataFrame(unit_rows)
        
        # Get Community Dragon data for native traits
        try:
            cd_response = requests.get('https://raw.communitydragon.org/latest/cdragon/tft/en_us.json', timeout=10)
            cd_data = cd_response.json()
        except Exception as e:
            print(f"Warning: Could not fetch Community Dragon data: {e}")
            cd_data = {}
        
        if unit_name:
            # Analyze specific unit
            result = analyze_unit(unit_df, unit_name, cd_data)
            return result
        else:
            # Get top units by frequency
            unit_counts = unit_df['unit'].value_counts().head(10)
            top_units = []
            
            for unit, count in unit_counts.items():
                if count >= 3:  # Only analyze units with at least 3 games
                    analysis = analyze_unit(unit_df, unit, cd_data, top_n=5, min_games=2)
                    if 'error' not in analysis:
                        analysis['total_games'] = int(count)
                        top_units.append(analysis)
            
            return {
                'total_games_analyzed': len(df),
                'total_unit_instances': len(unit_df),
                'top_units': top_units[:10]  # Return top 10 units
            }
        
    except Exception as e:
        print(f"Units analysis failed: {str(e)}")
        raise