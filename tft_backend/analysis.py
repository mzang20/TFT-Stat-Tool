import os
import requests
import time
import pandas as pd
from dotenv import load_dotenv
from collections import Counter, defaultdict

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
MASS_REGION = "americas"
TFT_SET = 13  # Set number for filtering matches

def get_match_ids(puuid):
    if not API_KEY:
        raise Exception("RIOT_API_KEY not found in environment variables")
    
    # Increase match count to get more Set 13 data
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
            # Handle rate limit on initial request
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
                
                # Filter by TFT set
                game_version = data.get('info', {}).get('tft_set_core_name', '')
                if game_version:
                    # Extract set number from game version (e.g., "TFTSet13_Anvil" -> 13)
                    try:
                        set_number = int(''.join(filter(str.isdigit, game_version.split('Set')[1] if 'Set' in game_version else '')))
                        if set_number != TFT_SET:
                            print(f"Match {match_id}: Wrong set (Set {set_number}, looking for Set {TFT_SET})")
                            return None
                    except (IndexError, ValueError):
                        print(f"Match {match_id}: Could not parse set number from {game_version}")
                        return None
                
                return data
            elif resp.status_code == 429:
                wait_time = 8 + (attempt * 4)  # Progressive backoff: 8s, 12s
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
        print(f"Starting analysis for PUUID: {puuid[:8]} (TFT Set {TFT_SET})...")
        
        # Get match IDs
        match_ids = get_match_ids(puuid)
        if not match_ids:
            raise Exception("No match IDs found")
        
        # Process more matches to account for set filtering
        matches_to_process = 50
        print(f"Processing {matches_to_process} matches...")
        
        data = {'placement': [], 'traits': []}
        successful_matches = 0
        set_filtered_matches = 0
        
        for i, match_id in enumerate(match_ids[:matches_to_process]):
            if i > 0 and i % 10 == 0:  # Rate limiting pause every 10 matches
                print(f"Processed {i} matches, brief pause...")
                time.sleep(3)
            
            match_data = get_match_data(match_id)
            if not match_data:
                continue
            
            set_filtered_matches += 1
            
            try:
                # Find player data
                player_data = None
                for participant in match_data['info']['participants']:
                    if participant.get('puuid') == puuid:
                        player_data = participant
                        break
                
                if not player_data:
                    print(f"Player not found in match {match_id}")
                    continue
                
                # Extract data safely
                placement = player_data.get('placement')
                traits = player_data.get('traits', [])
                
                if placement is None or not isinstance(placement, int):
                    print(f"Invalid placement in match {match_id}")
                    continue
                
                # Extract trait names safely
                trait_names = []
                for trait in traits:
                    if isinstance(trait, dict) and 'name' in trait:
                        trait_names.append(trait['name'])
                
                data['placement'].append(placement)
                data['traits'].append(trait_names)
                successful_matches += 1
                
            except Exception as e:
                print(f"Error processing match {match_id}: {str(e)}")
                continue
        
        if successful_matches < 3:  # Need minimum matches for analysis
            raise Exception(f"Insufficient Set {TFT_SET} data - only {successful_matches} valid matches found (found {set_filtered_matches} Set {TFT_SET} matches total)")
        
        print(f"Successfully processed {successful_matches} Set {TFT_SET} matches")
        
        # Analyze traits
        df = pd.DataFrame(data)
        
        # Count all traits
        all_traits = []
        for traits_list in df['traits']:
            all_traits.extend(traits_list)
        
        trait_counts = Counter(all_traits)
        
        min_appearances = 10
        valid_traits = {trait for trait, count in trait_counts.items() if count >= min_appearances}
        
        if not valid_traits:
            raise Exception("No traits found with sufficient frequency")
        
        # Filter traits per match
        df['filtered_traits'] = df['traits'].apply(
            lambda traits: [trait for trait in traits if trait in valid_traits]
        )
        
        # Calculate statistics
        trait_stats = {}
        for trait in valid_traits:
            top_4_count = 0
            bot_4_count = 0
            total_count = 0
            
            for _, row in df.iterrows():
                if trait in row['filtered_traits']:
                    total_count += 1
                    if row['placement'] <= 4:
                        top_4_count += 1
                    else:
                        bot_4_count += 1
            
            if total_count > 0:
                trait_stats[trait] = {
                    'Trait': trait,
                    'Top 4 Rate': top_4_count / total_count,
                    'Bottom 4 Rate': bot_4_count / total_count,
                    'Games Played': total_count
                }
        
        if not trait_stats:
            raise Exception("No trait statistics available")
        
        # Convert to list and sort
        trait_list = list(trait_stats.values())
        trait_df = pd.DataFrame(trait_list)
        
        # Get top and bottom performing traits
        top_traits = trait_df.sort_values('Top 4 Rate', ascending=False).head(8).to_dict(orient='records')
        bottom_traits = trait_df.sort_values('Bottom 4 Rate', ascending=False).head(8).to_dict(orient='records')
        
        print(f"Analysis complete for Set {TFT_SET} - {len(top_traits)} top traits, {len(bottom_traits)} bottom traits")
        
        return top_traits, bottom_traits
        
    except Exception as e:
        print(f"Analysis failed: {str(e)}")
        raise