# analysis.py

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
    url = f"https://{MASS_REGION}.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids?start=0&count=50&api_key={API_KEY}"
    resp = requests.get(url)
    return resp.json()

def get_match_data(match_id):
    url = f"https://{MASS_REGION}.api.riotgames.com/tft/match/v1/matches/{match_id}?api_key={API_KEY}"
    while True:
        resp = requests.get(url)
        if resp.status_code == 429:
            time.sleep(10)
            continue
        return resp.json()

def run_analysis(puuid):
    match_ids = get_match_ids(puuid)
    data = {'placement': [], 'traits': []}
    
    for match_id in match_ids:
        match_data = get_match_data(match_id)
        player_data = next(p for p in match_data['info']['participants'] if p['puuid'] == puuid)
        data['placement'].append(player_data['placement'])
        data['traits'].append([t['name'] for t in player_data['traits']])

    df = pd.DataFrame(data)

    trait_counts = Counter([trait for traits in df['traits'] for trait in traits])
    valid_traits = {t for t, count in trait_counts.items() if count > 10}
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

    trait_data = []
    for trait in total_count:
        trait_data.append({
            'Trait': trait,
            'Top 4 Rate': top_count[trait] / total_count[trait],
            'Bottom 4 Rate': bot_count[trait] / total_count[trait],
            'Games Played': total_count[trait]
        })

    trait_df = pd.DataFrame(trait_data)
    top_4 = trait_df.sort_values('Top 4 Rate', ascending=False).head(10).to_dict(orient='records')
    bot_4 = trait_df.sort_values('Bottom 4 Rate', ascending=False).head(10).to_dict(orient='records')
    return top_4, bot_4
