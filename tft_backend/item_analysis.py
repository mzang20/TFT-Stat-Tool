import os
import requests
import time
import pandas as pd
from dotenv import load_dotenv
from collections import Counter, defaultdict

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

def run_analysis(puuid):
    try:
        print(f"Starting item analysis for PUUID: {puuid[:8]} (TFT Set {TFT_SET})...")
        
        # Get match IDs
        match_ids = get_match_ids(puuid)
        if not match_ids:
            raise Exception("No match IDs found")
        
        print(f"Processing {len(match_ids)} matches...")
        
        # Use the exact same data structure as your trait_analysis.py
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
            if i > 0 and i % 10 == 0:  # Rate limiting pause every 10 matches
                print(f"Processed {i} matches, brief pause...")
                time.sleep(3)
            
            match_data = get_match_data(match_id)
            if not match_data:
                continue
            
            try:
                # Extract set number like original
                set_number = match_data['info']['tft_set_number']
                data['set_number'].append(set_number)
                
                # Find player index in metadata participants like original
                index = None
                for pos, participant_puuid in enumerate(match_data['metadata']['participants']):
                    if puuid == participant_puuid:
                        index = pos
                        break
                
                if index is None:
                    print(f"Player not found in match {match_id}")
                    data['set_number'].pop()  # Remove the set_number we just added
                    continue
                
                # Extract data using the same structure as original
                participant_data = match_data['info']['participants'][index]
                
                placement = participant_data['placement']
                level = participant_data['level']
                traits = [trait['name'] for trait in participant_data['traits']]
                units = [unit['character_id'] for unit in participant_data['units']]
                items = [item.get('itemNames', []) for item in participant_data['units']]
                
                # Add to dataset like original
                data['placement'].append(placement)
                data['level'].append(level)
                data['traits'].append(traits)
                data['units'].append(units)
                data['items'].append(items)
                
                successful_matches += 1
                
            except Exception as e:
                print(f"Error processing match {match_id}: {str(e)}")
                # Remove the set_number if we added it but failed later
                if len(data['set_number']) > len(data['placement']):
                    data['set_number'].pop()
                continue
        
        if successful_matches < 3:
            raise Exception(f"Insufficient data - only {successful_matches} valid matches found")
        
        print(f"Successfully processed {successful_matches} matches")
        
        # Create DataFrame and filter by set like original
        df = pd.DataFrame(data)
        df = df[df['set_number'] == TFT_SET].copy()  # Filter by set AFTER creating DataFrame
        
        if len(df) < 3:
            raise Exception(f"Insufficient Set {TFT_SET} data - only {len(df)} matches from Set {TFT_SET}")
        
        print(f"Found {len(df)} Set {TFT_SET} matches")
        
        # ITEMS ANALYSIS (using your exact logic pattern from trait_analysis.py)
        # Step 1: Flatten all items and count appearances
        item_counts = Counter(
            item
            for item_lists in df['items']
            for unit_items in item_lists
            for item in unit_items
        )

        # Step 2: Filter out items with <=10 total appearances (match original threshold)
        valid_items = {item for item, count in item_counts.items() if count > 10}

        if not valid_items:
            raise Exception("No items found with sufficient frequency")

        # Step 3: Create a new column with filtered items per game
        def filter_items(item_lists):
            return [[item for item in unit_items if item in valid_items] for unit_items in item_lists]

        df['filtered_items'] = df['items'].apply(filter_items)

        # Step 4: Calculate win/lose percentages using the EXACT same logic as trait_analysis.py
        item_top_count = defaultdict(int)
        item_bot_count = defaultdict(int)
        item_total_count = defaultdict(int)

        # Count item stats across filtered data
        for _, row in df.iterrows():
            is_top4 = row['placement'] <= 4
            is_bot4 = not is_top4

            for unit_items in row['filtered_items']:
                for item in unit_items:
                    item_total_count[item] += 1
                    if is_top4:
                        item_top_count[item] += 1
                    else:
                        item_bot_count[item] += 1

        # Step 5: Create summary DataFrame like original
        item_data = []
        for item in item_total_count:
            top_rate = item_top_count[item] / item_total_count[item]
            bot_rate = item_bot_count[item] / item_total_count[item]
            item_data.append({
                'Item': item,
                'Top 4 Rate': top_rate,
                'Bottom 4 Rate': bot_rate,
                'Games Played': item_total_count[item]
            })

        item_df = pd.DataFrame(item_data)
        
        # Get top 10 of each like original (not 8)
        top_items = item_df.sort_values(by='Top 4 Rate', ascending=False).head(10).to_dict(orient='records')
        bottom_items = item_df.sort_values(by='Bottom 4 Rate', ascending=False).head(10).to_dict(orient='records')
        
        print(f"Item analysis complete for Set {TFT_SET} - {len(top_items)} top items, {len(bottom_items)} bottom items")
        
        return top_items, bottom_items
        
    except Exception as e:
        print(f"Item analysis failed: {str(e)}")
        raise