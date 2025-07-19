from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import pandas as pd
import time
import json

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)

RIOT_API_KEY = os.getenv("RIOT_API_KEY")
RIOT_PUUID = os.getenv("RIOT_PUUID")  # fallback default if needed

# --------- TFT Logic ---------

def get_match_ids(puuid, mass_region, api_key):
    url = f"https://{mass_region}.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids?start=0&count=50&api_key={api_key}"
    resp = requests.get(url)
    return resp.json()

def get_match_data(match_id, mass_region, api_key):
    url = f"https://{mass_region}.api.riotgames.com/tft/match/v1/matches/{match_id}?api_key={api_key}"
    while True:
        resp = requests.get(url)
        if resp.status_code == 429:
            time.sleep(10)
            continue
        return resp.json()

def gather_all_data(puuid, match_ids, mass_region, api_key):
    data = {'set_number': [], 'placement': [], 'level': [], 'traits': [], 'units': [], 'items': []}
    for match_id in match_ids:
        match_data = get_match_data(match_id, mass_region, api_key)
        index = match_data['metadata']['participants'].index(puuid)
        participant = match_data['info']['participants'][index]
        data['set_number'].append(match_data['info']['tft_set_number'])
        data['placement'].append(participant['placement'])
        data['level'].append(participant['level'])
        data['traits'].append([t['name'] for t in participant['traits']])
        data['units'].append([u['character_id'] for u in participant['units']])
        data['items'].append([u['itemNames'] for u in participant['units']])
    return pd.DataFrame(data)

def analyze_traits(df):
    from collections import Counter, defaultdict
    df = df[df['set_number'] == 13].copy()
    trait_counts = Counter([trait for traits in df['traits'] for trait in traits])
    valid_traits = {trait for trait, count in trait_counts.items() if count > 10}
    df['filtered_traits'] = df['traits'].apply(lambda traits: [t for t in traits if t in valid_traits])
    trait_top_count = defaultdict(int)
    trait_bot_count = defaultdict(int)
    trait_total_count = defaultdict(int)
    for _, row in df.iterrows():
        is_top4 = row['placement'] <= 4
        for trait in row['filtered_traits']:
            trait_total_count[trait] += 1
            if is_top4:
                trait_top_count[trait] += 1
            else:
                trait_bot_count[trait] += 1
    trait_data = []
    for trait in trait_total_count:
        top_rate = trait_top_count[trait] / trait_total_count[trait]
        bot_rate = trait_bot_count[trait] / trait_total_count[trait]
        trait_data.append({
            'Trait': trait,
            'Top 4 Rate': top_rate,
            'Bottom 4 Rate': bot_rate,
            'Games Played': trait_total_count[trait]
        })
    trait_df = pd.DataFrame(trait_data)
    top_4_df = trait_df.sort_values(by='Top 4 Rate', ascending=False).head(10)
    bot_4_df = trait_df.sort_values(by='Bottom 4 Rate', ascending=False).head(10)
    return top_4_df.to_dict(orient='records'), bot_4_df.to_dict(orient='records')

# --------- API Routes ---------

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    puuid = data.get("puuid") or RIOT_PUUID
    match_ids = get_match_ids(puuid, "americas", RIOT_API_KEY)
    df = gather_all_data(puuid, match_ids, "americas", RIOT_API_KEY)
    top_4, bot_4 = analyze_traits(df)
    return jsonify({"top_4_traits": top_4, "bottom_4_traits": bot_4})

# --------- Run ---------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)