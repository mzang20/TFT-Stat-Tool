import os
import requests
import time
import pandas as pd
from dotenv import load_dotenv
from collections import Counter, defaultdict

# Flask imports
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import sys

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
MASS_REGION = "americas"
TFT_SET = 13  # Set number for filtering matches

def get_match_ids(puuid):
    if not API_KEY:
        raise Exception("RIOT_API_KEY not found in environment variables")
    
    # Match the original count=50
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
                
                return data  # Return all data, filter by set later like original
            elif resp.status_code == 429:
                wait_time = 10  # Match original sleep time
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
        
        print(f"Processing {len(match_ids)} matches...")
        
        # Use the exact same data structure as original
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
        
        # Count all trait appearances like original
        trait_counts = Counter([trait for traits in df['traits'] for trait in traits])
        
        # Filter out traits with <=10 total appearances (match original threshold)
        valid_traits = {trait for trait, count in trait_counts.items() if count > 10}
        
        if not valid_traits:
            raise Exception("No traits found with sufficient frequency")
        
        # Create filtered traits column like original
        df['filtered_traits'] = df['traits'].apply(lambda traits: [t for t in traits if t in valid_traits])
        
        # Calculate win/lose percentages using the EXACT same logic as original
        trait_top_count = defaultdict(int)
        trait_bot_count = defaultdict(int)
        trait_total_count = defaultdict(int)

        # Count trait stats across filtered data
        for _, row in df.iterrows():
            is_top4 = row['placement'] <= 4
            is_bot4 = not is_top4

            for trait in row['filtered_traits']:
                trait_total_count[trait] += 1
                if is_top4:
                    trait_top_count[trait] += 1
                else:
                    trait_bot_count[trait] += 1

        # Create summary DataFrame like original
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
        
        # Get top 10 of each like original (not 8)
        top_traits = trait_df.sort_values(by='Top 4 Rate', ascending=False).head(10).to_dict(orient='records')
        bottom_traits = trait_df.sort_values(by='Bottom 4 Rate', ascending=False).head(10).to_dict(orient='records')
        
        print(f"Analysis complete for Set {TFT_SET} - {len(top_traits)} top traits, {len(bottom_traits)} bottom traits")
        
        return top_traits, bottom_traits
        
    except Exception as e:
        print(f"Analysis failed: {str(e)}")
        raise

# ===============================
# FLASK WEB SERVER
# ===============================

app = Flask(__name__)
CORS(app, origins=["*"])

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.route('/api/analyze', methods=['POST'])
def analyze_player():
    """
    Analyze a player's TFT trait performance
    Expected JSON body: {"puuid": "player_puuid"}
    Returns: {"top_traits": [...], "bottom_traits": [...]}
    """
    try:
        # Get PUUID from request
        data = request.get_json()
        
        if not data or 'puuid' not in data:
            return jsonify({'error': 'PUUID is required'}), 400
        
        puuid = data['puuid'].strip()
        
        if not puuid:
            return jsonify({'error': 'PUUID cannot be empty'}), 400
        
        # Basic PUUID validation
        if len(puuid) < 20:
            return jsonify({'error': 'Invalid PUUID format'}), 400
        
        logger.info(f"Starting analysis for PUUID: {puuid[:8]}...")
        
        # Run the analysis
        top_traits, bottom_traits = run_analysis(puuid)
        
        # Return the results
        result = {
            'top_traits': top_traits,
            'bottom_traits': bottom_traits,
            'puuid': puuid[:8] + '...',
            'message': 'Analysis completed successfully'
        }
        
        logger.info(f"Analysis completed successfully for {puuid[:8]}")
        return jsonify(result), 200
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Analysis failed: {error_message}")
        
        # Return appropriate error messages
        if "API key" in error_message:
            return jsonify({'error': 'API configuration error'}), 500
        elif "PUUID not found" in error_message:
            return jsonify({'error': 'PUUID not found or no matches available'}), 404
        elif "Rate limited" in error_message:
            return jsonify({'error': 'Rate limited by Riot API. Please try again in a few minutes.'}), 429
        elif "Insufficient" in error_message:
            return jsonify({'error': 'Not enough Set 13 matches found for analysis. Play more ranked games and try again.'}), 400
        elif "Network error" in error_message or "timeout" in error_message.lower():
            return jsonify({'error': 'Network error. Please check your connection and try again.'}), 503
        else:
            return jsonify({'error': f'Analysis failed: {error_message}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'message': 'TFT Analysis API is running',
        'api_key_configured': bool(API_KEY)
    }), 200

@app.route('/analyze', methods=['GET'])
def analyze_player_get():
    """Alternative GET endpoint for testing"""
    try:
        puuid = request.args.get('puuid')
        if not puuid:
            return jsonify({'error': 'PUUID parameter is required'}), 400
        
        top_traits, bottom_traits = run_analysis(puuid)
        
        return jsonify({
            'top_traits': top_traits,
            'bottom_traits': bottom_traits,
            'message': 'Analysis completed successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Check configuration on startup
    if not API_KEY:
        print("⚠️  WARNING: RIOT_API_KEY not configured. Add it to your .env file.")
    else:
        print("✅ Riot API key configured")
    
    print("🚀 Starting TFT Analysis API server...")
    print("📍 Health check: http://localhost:5000/api/health")
    print("📊 Analysis endpoint: POST http://localhost:5000/api/analyze")
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)