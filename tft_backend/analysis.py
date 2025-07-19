import os
import requests
import time
import pandas as pd
from dotenv import load_dotenv
from collections import Counter, defaultdict

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
MASS_REGION = "americas"

def get_match_ids(puuid):
    if not API_KEY:
        raise Exception("RIOT_API_KEY not found in environment variables")
    
    url = f"https://{MASS_REGION}.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids?start=0&count=50&api_key={API_KEY}"
    print(f"Requesting match IDs from: {url}")
    
    try:
        resp = requests.get(url, timeout=10)
        print(f"Match IDs response: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"Error getting match IDs: {resp.status_code} - {resp.text}")
            if resp.status_code == 401:
                raise Exception("Invalid API key")
            elif resp.status_code == 404:
                raise Exception("PUUID not found or no matches available")
            else:
                raise Exception(f"API error: {resp.status_code} - {resp.text}")
        
        data = resp.json()
        print(f"Found {len(data)} matches")
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Network error: {str(e)}")
        raise Exception(f"Network error while fetching match IDs: {str(e)}")

def get_match_data(match_id):
    url = f"https://{MASS_REGION}.api.riotgames.com/tft/match/v1/matches/{match_id}?api_key={API_KEY}"
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            resp = requests.get(url, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                # Check if the response has the expected structure
                if 'info' not in data:
                    print(f"Warning: Match {match_id} missing 'info' key. Response keys: {list(data.keys())}")
                    return None
                return data
            elif resp.status_code == 429:
                print(f"Rate limited, waiting 10 seconds... (retry {retry_count + 1})")
                time.sleep(10)
                retry_count += 1
            elif resp.status_code == 404:
                print(f"Match {match_id} not found (404)")
                return None
            else:
                print(f"Error getting match data for {match_id}: {resp.status_code} - {resp.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Network error for match {match_id}: {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(5)
    
    print(f"Failed to get match data for {match_id} after {max_retries} retries")
    return None

def run_analysis(puuid):
    try:
        match_ids = get_match_ids(puuid)
        
        if not match_ids:
            raise Exception("No match IDs found for this PUUID")
        
        data = {'placement': [], 'traits': []}
        successful_matches = 0
        
        for match_id in match_ids:
            match_data = get_match_data(match_id)
            
            # Skip if match data is invalid
            if not match_data or 'info' not in match_data:
                print(f"Skipping match {match_id} - invalid data")
                continue
            
            try:
                # Find the player's data
                player_data = None
                for participant in match_data['info']['participants']:
                    if participant['puuid'] == puuid:
                        player_data = participant
                        break
                
                if not player_data:
                    print(f"Player not found in match {match_id}")
                    continue
                
                # Extract placement and traits
                placement = player_data.get('placement')
                traits = player_data.get('traits', [])
                
                if placement is None:
                    print(f"No placement data for match {match_id}")
                    continue
                
                data['placement'].append(placement)
                data['traits'].append([t['name'] for t in traits if 'name' in t])
                successful_matches += 1
                
            except Exception as e:
                print(f"Error processing match {match_id}: {str(e)}")
                continue
        
        if successful_matches == 0:
            raise Exception("No valid match data found")
        
        print(f"Successfully processed {successful_matches} out of {len(match_ids)} matches")
        
        # Continue with the analysis
        df = pd.DataFrame(data)
        
        trait_counts = Counter([trait for traits in df['traits'] for trait in traits])
        valid_traits = {t for t, count in trait_counts.items() if count > 5}  # Lowered threshold
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
            if total_count[trait] > 0:  # Avoid division by zero
                trait_data.append({
                    'Trait': trait,
                    'Top 4 Rate': top_count[trait] / total_count[trait],
                    'Bottom 4 Rate': bot_count[trait] / total_count[trait],
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