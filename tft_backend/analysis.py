import os
import requests
import time
import pandas as pd
from dotenv import load_dotenv
from collections import Counter, defaultdict

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
MASS_REGION = "americas"

# Debug: Check if API key is loaded
if not API_KEY:
    print("ERROR: RIOT_API_KEY not found in environment variables")
    raise Exception("RIOT_API_KEY not configured")

def get_match_ids(puuid):
    api_url_match = (
        "https://" +
        MASS_REGION +
        ".api.riotgames.com/tft/match/v1/matches/by-puuid/" +
        puuid + 
        "/ids?start=0&count=50" + 
        "&api_key=" + 
        API_KEY
    )
    
    resp = requests.get(api_url_match)
    
    if resp.status_code != 200:
        print(f"Error getting match IDs: {resp.status_code} - {resp.text}")
        raise Exception(f"Failed to get match IDs: {resp.status_code}")
    
    return resp.json()

def get_match_data(match_id):
    api_url_matchdata = (
        "https://" + 
        MASS_REGION + 
        ".api.riotgames.com/tft/match/v1/matches/" +
        match_id + 
        "?api_key=" + 
        API_KEY
    )
    
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        resp = requests.get(api_url_matchdata)
        
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 429:
            print(f"Rate Limit hit, sleeping for 10 seconds")
            time.sleep(10)
            retry_count += 1
        else:
            print(f"Error getting match data for {match_id}: {resp.status_code} - {resp.text}")
            return None
    
    print(f"Failed to get match data for {match_id} after {max_retries} retries")
    return None

def run_analysis(puuid):
    try:
        match_ids = get_match_ids(puuid)
        
        if not match_ids:
            raise Exception("No match IDs found for this PUUID")
        
        # We initialize an empty dictionary to store data for each game
        data = {
            'set_number': [],
            'placement': [],
            'traits': []
        }
        
        successful_matches = 0
        
        for match_id in match_ids:
            match_data = get_match_data(match_id)
            
            if not match_data or 'info' not in match_data or 'metadata' not in match_data:
                print(f"Skipping match {match_id} - invalid data structure")
                continue
            
            try:
                # Find the player index using metadata participants (like your original code)
                index = None
                for pos, participant_puuid in enumerate(match_data['metadata']['participants']):
                    if puuid == participant_puuid:
                        index = pos
                        break
                
                if index is None:
                    print(f"Player not found in match {match_id}")
                    continue
                
                # Extract data using the index (like your original code)
                set_number = match_data['info']['tft_set_number']
                placement = match_data['info']['participants'][index]['placement']
                traits = [trait['name'] for trait in match_data['info']['participants'][index]['traits']]
                
                # Add to our dataset
                data['set_number'].append(set_number)
                data['placement'].append(placement)
                data['traits'].append(traits)
                
                successful_matches += 1
                
            except Exception as e:
                print(f"Error processing match {match_id}: {str(e)}")
                continue
        
        if successful_matches == 0:
            raise Exception("No valid match data found")
        
        print(f"Successfully processed {successful_matches} out of {len(match_ids)} matches")
        
        # Create DataFrame and filter for current set (like your original code)
        df = pd.DataFrame(data)
        current_set = 13
        df = df[df['set_number'] == current_set].copy()
        
        if df.empty:
            raise Exception(f"No matches found for set {current_set}")
        
        # Continue with trait analysis
        trait_counts = Counter([trait for traits in df['traits'] for trait in traits])
        valid_traits = {t for t, count in trait_counts.items() if count >= 3}  # Lower threshold
        df['filtered'] = df['traits'].apply(lambda traits: [t for t in traits if t in valid_traits])
        
        top_count = defaultdict(int)
        bot_count = defaultdict(int)
        total_count = defaultdict(int)
        
        for _, row in df.iterrows():
            is_top = row['placement'] <= 4
            for trait in row['filtered']:
                total_count[trait] += 1
                if is_top:
                    top_count[trait] += 1
                else:
                    bot_count[trait] += 1
        
        if not total_count:
            raise Exception("No traits found with sufficient data")
        
        trait_data = []
        for trait in total_count:
            if total_count[trait] > 0:
                trait_data.append({
                    'Trait': trait,
                    'Top 4 Rate': round(top_count[trait] / total_count[trait], 3),
                    'Bottom 4 Rate': round(bot_count[trait] / total_count[trait], 3),
                    'Games Played': total_count[trait]
                })
        
        if not trait_data:
            raise Exception("No trait data available for analysis")
        
        trait_df = pd.DataFrame(trait_data)
        top_4 = trait_df.sort_values('Top 4 Rate', ascending=False).head(10).to_dict(orient='records')
        bot_4 = trait_df.sort_values('Bottom 4 Rate', ascending=False).head(10).to_dict(orient='records')
        
        return top_4, bot_4
        
    except Exception as e:
        print(f"Analysis error: {str(e)}")
        raise