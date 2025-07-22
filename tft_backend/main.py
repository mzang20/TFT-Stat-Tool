import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from trait_analysis import run_analysis as run_trait_analysis
from item_analysis import run_analysis as run_item_analysis
from unit_analysis import run_analysis as run_units_analysis
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
MASS_REGION = "americas"

# Import and override the TFT_SET from analysis modules
import trait_analysis as trait_analysis
import item_analysis as item_analysis
import unit_analysis as unit_analysis
trait_analysis.TFT_SET = 14  # Force Set 14
item_analysis.TFT_SET = 14   # Force Set 14
unit_analysis.TFT_SET = 14   # Force Set 14

app = Flask(__name__)
CORS(app)

def get_puuid_from_riot_id(game_name, tag_line):
    if not API_KEY:
        raise Exception("RIOT_API_KEY not found in environment variables")
    
    url = f"https://{MASS_REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}?api_key={API_KEY}"
    print(f"Getting PUUID for {game_name}#{tag_line}...")
    
    try:
        resp = requests.get(url, timeout=15)
        print(f"Riot ID response: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            puuid = data.get('puuid')
            if puuid:
                print(f"Found PUUID: {puuid[:8]}...")
                return puuid
            else:
                raise Exception("PUUID not found in response")
        elif resp.status_code == 404:
            raise Exception("Riot ID not found - check your game name and tag line")
        elif resp.status_code == 401:
            raise Exception("Invalid API key")
        elif resp.status_code == 429:
            raise Exception("Rate limited - please try again in a few minutes")
        else:
            raise Exception(f"API error: {resp.status_code}")
        
    except requests.exceptions.Timeout:
        raise Exception("Request timed out - API may be slow, try again")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error: {str(e)}")


@app.route('/')
def health_check():
    return jsonify({
        "status": "TFT Analysis API is running - Set 14",
        "tft_set": trait_analysis.TFT_SET,
        "api_key_configured": bool(API_KEY),
        "endpoints": {
            "traits_by_puuid": "/analyze-traits?puuid=YOUR_PUUID",
            "traits_by_riot_id": "/analyze-traits-riot-id?gameName=GAME_NAME&tagLine=TAG_LINE",
            "items_by_puuid": "/analyze-items?puuid=YOUR_PUUID", 
            "items_by_riot_id": "/analyze-items-riot-id?gameName=GAME_NAME&tagLine=TAG_LINE",
            "units_by_puuid": "/analyze-units?puuid=YOUR_PUUID",
            "units_by_riot_id": "/analyze-units-riot-id?gameName=GAME_NAME&tagLine=TAG_LINE",
            "combined_analysis": "/analyze-all-riot-id?gameName=GAME_NAME&tagLine=TAG_LINE"
        }
    })

# COMBINED ANALYSIS (NEW - RECOMMENDED)
@app.route('/analyze-all-riot-id')
def analyze_all_by_riot_id():
    try:
        game_name = request.args.get('gameName')
        tag_line = request.args.get('tagLine')
        
        if not game_name or not tag_line:
            return jsonify({'error': 'Both gameName and tagLine parameters are required'}), 400
        
        game_name = game_name.strip()
        tag_line = tag_line.strip()
        
        if not game_name or not tag_line:
            return jsonify({'error': 'Game name and tag line cannot be empty'}), 400
        
        print(f"Starting combined analysis for Riot ID: {game_name}#{tag_line}")
        
        # Get PUUID once
        puuid = get_puuid_from_riot_id(game_name, tag_line)
        
        # Run all three analyses (they'll share the same match data fetching)
        traits_success = True
        items_success = True
        units_success = True
        
        try:
            print("Running traits analysis...")
            top_traits, bottom_traits = run_trait_analysis(puuid)
            print(f"Traits analysis completed - {len(top_traits)} top traits")
        except Exception as e:
            print(f"Traits analysis failed: {e}")
            top_traits, bottom_traits = [], []
            traits_success = False
        
        try:
            print("Running items analysis...")
            top_items, bottom_items = run_item_analysis(puuid)
            print(f"Items analysis completed - {len(top_items)} top items")
        except Exception as e:
            print(f"Items analysis failed: {e}")
            top_items, bottom_items = [], []
            items_success = False
            
        # UNITS ANALYSIS - Replace your current units section with this:
        try:
            print("Running units analysis...")
            units_results = run_units_analysis(puuid)
            
            # Check if we got valid results
            if units_results and units_results.get('top_units') and len(units_results.get('top_units', [])) > 0:
                print(f"Units analysis completed - {len(units_results.get('top_units', []))} units analyzed")
                units_success = True
            else:
                print("Units analysis returned empty results")
                units_success = False
                units_results = {'top_units': [], 'total_games_analyzed': 0, 'total_unit_instances': 0}
                
        except Exception as e:
            print(f"Units analysis failed: {e}")
            units_results = {'top_units': [], 'total_games_analyzed': 0, 'total_unit_instances': 0}
            units_success = False
        
        # Check if at least one analysis succeeded
        if not (traits_success or items_success or units_success):
            return jsonify({'error': 'All analyses failed. Please try again later.'}), 500
        
        # Return combined results
        result = {
            'traits': {
                'top_traits': top_traits,
                'bottom_traits': bottom_traits,
                'success': traits_success
            },
            'items': {
                'top_items': top_items,
                'bottom_items': bottom_items,
                'success': items_success
            },
            'units': {
                **units_results,
                'success': units_success
            },
            'riot_id': f"{game_name}#{tag_line}",
            'puuid': puuid[:8] + '...',
            'tft_set': trait_analysis.TFT_SET,
            'message': 'Combined analysis completed',
            'analyses_completed': {
                'traits': traits_success,
                'items': items_success,
                'units': units_success
            }
        }
        
        print(f"Combined analysis completed for {game_name}#{tag_line}")
        print(f"Success: Traits={traits_success}, Items={items_success}, Units={units_success}")
        return jsonify(result), 200
        
    except Exception as e:
        return _handle_analysis_error(e, "combined")

# TRAIT ANALYSIS
@app.route('/analyze-traits-riot-id')
def analyze_traits_by_riot_id():
    try:
        game_name = request.args.get('gameName')
        tag_line = request.args.get('tagLine')
        
        if not game_name or not tag_line:
            return jsonify({'error': 'Both gameName and tagLine parameters are required'}), 400
        
        game_name = game_name.strip()
        tag_line = tag_line.strip()
        
        if not game_name or not tag_line:
            return jsonify({'error': 'Game name and tag line cannot be empty'}), 400
        
        print(f"Starting Set {trait_analysis.TFT_SET} trait analysis for Riot ID: {game_name}#{tag_line}")
        
        # First, get the PUUID from Riot ID
        puuid = get_puuid_from_riot_id(game_name, tag_line)
        
        # Then run the trait analysis with the PUUID
        top_traits, bottom_traits = run_trait_analysis(puuid)
        
        # Return the results
        result = {
            'top_traits': top_traits,
            'bottom_traits': bottom_traits,
            'riot_id': f"{game_name}#{tag_line}",
            'puuid': puuid[:8] + '...',
            'tft_set': trait_analysis.TFT_SET,
            'analysis_type': 'traits',
            'message': f'Set {trait_analysis.TFT_SET} trait analysis completed successfully'
        }
        
        print(f"Set {trait_analysis.TFT_SET} trait analysis completed successfully for {game_name}#{tag_line}")
        return jsonify(result), 200
        
    except Exception as e:
        return _handle_analysis_error(e, "trait")

@app.route('/analyze-traits')
def analyze_traits():
    puuid = request.args.get('puuid')
    if not puuid:
        return jsonify({"error": "Missing PUUID"}), 400
    
    try:
        top, bot = run_trait_analysis(puuid)
        return jsonify({
            "top_traits": top,
            "bottom_traits": bot,
            "puuid": puuid[:8] + '...',
            "tft_set": trait_analysis.TFT_SET,
            "analysis_type": "traits",
            "message": f"Set {trait_analysis.TFT_SET} trait analysis completed successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ITEM ANALYSIS
@app.route('/analyze-items-riot-id')
def analyze_items_by_riot_id():
    try:
        game_name = request.args.get('gameName')
        tag_line = request.args.get('tagLine')
        
        if not game_name or not tag_line:
            return jsonify({'error': 'Both gameName and tagLine parameters are required'}), 400
        
        game_name = game_name.strip()
        tag_line = tag_line.strip()
        
        if not game_name or not tag_line:
            return jsonify({'error': 'Game name and tag line cannot be empty'}), 400
        
        print(f"Starting Set {item_analysis.TFT_SET} item analysis for Riot ID: {game_name}#{tag_line}")
        
        # First, get the PUUID from Riot ID
        puuid = get_puuid_from_riot_id(game_name, tag_line)
        
        # Then run the item analysis with the PUUID
        top_items, bottom_items = run_item_analysis(puuid)
        
        # Return the results
        result = {
            'top_items': top_items,
            'bottom_items': bottom_items,
            'riot_id': f"{game_name}#{tag_line}",
            'puuid': puuid[:8] + '...',
            'tft_set': item_analysis.TFT_SET,
            'analysis_type': 'items',
            'message': f'Set {item_analysis.TFT_SET} item analysis completed successfully'
        }
        
        print(f"Set {item_analysis.TFT_SET} item analysis completed successfully for {game_name}#{tag_line}")
        return jsonify(result), 200
        
    except Exception as e:
        return _handle_analysis_error(e, "item")

@app.route('/analyze-items')
def analyze_items():
    puuid = request.args.get('puuid')
    if not puuid:
        return jsonify({"error": "Missing PUUID"}), 400
    
    try:
        top, bot = run_item_analysis(puuid)
        return jsonify({
            "top_items": top,
            "bottom_items": bot,
            "puuid": puuid[:8] + '...',
            "tft_set": item_analysis.TFT_SET,
            "analysis_type": "items",
            "message": f"Set {item_analysis.TFT_SET} item analysis completed successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# UNITS ANALYSIS
@app.route('/analyze-units-riot-id')
def analyze_units_by_riot_id():
    try:
        game_name = request.args.get('gameName')
        tag_line = request.args.get('tagLine')
        unit_name = request.args.get('unit')  # Optional: analyze specific unit
        
        if not game_name or not tag_line:
            return jsonify({'error': 'Both gameName and tagLine parameters are required'}), 400
        
        game_name = game_name.strip()
        tag_line = tag_line.strip()
        
        if not game_name or not tag_line:
            return jsonify({'error': 'Game name and tag line cannot be empty'}), 400
        
        print(f"Starting Set {unit_analysis.TFT_SET} units analysis for Riot ID: {game_name}#{tag_line}")
        
        # First, get the PUUID from Riot ID
        puuid = get_puuid_from_riot_id(game_name, tag_line)
        
        # Then run the units analysis with the PUUID
        results = run_units_analysis(puuid, unit_name)
        
        # Return the results
        result = {
            **results,
            'riot_id': f"{game_name}#{tag_line}",
            'puuid': puuid[:8] + '...',
            'tft_set': unit_analysis.TFT_SET,
            'analysis_type': 'units',
            'message': f'Set {unit_analysis.TFT_SET} units analysis completed successfully'
        }
        
        print(f"Set {unit_analysis.TFT_SET} units analysis completed successfully for {game_name}#{tag_line}")
        return jsonify(result), 200
        
    except Exception as e:
        return _handle_analysis_error(e, "units")

@app.route('/analyze-units')
def analyze_units():
    puuid = request.args.get('puuid')
    unit_name = request.args.get('unit')  # Optional: analyze specific unit
    
    if not puuid:
        return jsonify({"error": "Missing PUUID"}), 400
    
    try:
        results = run_units_analysis(puuid, unit_name)
        return jsonify({
            **results,
            "puuid": puuid[:8] + '...',
            "tft_set": unit_analysis.TFT_SET,
            "analysis_type": "units",
            "message": f"Set {unit_analysis.TFT_SET} units analysis completed successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# LEGACY ENDPOINTS
@app.route('/analyze-riot-id')
def analyze_by_riot_id():
    return analyze_traits_by_riot_id()

@app.route('/analyze')
def analyze():
    return analyze_traits()

# HELPER FUNCTIONS
def _handle_analysis_error(e, analysis_type):
    error_message = str(e)
    print(f"{analysis_type.title()} analysis failed: {error_message}")
    
    # Return appropriate error messages
    if "API key" in error_message:
        return jsonify({'error': 'API configuration error'}), 500
    elif "Riot ID not found" in error_message:
        return jsonify({'error': 'Riot ID not found - check your game name and tag line'}), 404
    elif "Rate limited" in error_message:
        return jsonify({'error': 'Rate limited by Riot API. Please try again in a few minutes.'}), 429
    elif "Insufficient" in error_message:
        return jsonify({'error': f'Not enough Set {trait_analysis.TFT_SET} matches found for analysis. Play more ranked games and try again.'}), 400
    elif "Network error" in error_message or "timeout" in error_message.lower():
        return jsonify({'error': 'Network error. Please check your connection and try again.'}), 503
    else:
        return jsonify({'error': f'{analysis_type.title()} analysis failed: {error_message}'}), 500

if __name__ == "__main__":
    # Check configuration on startup
    if not API_KEY:
        print("⚠️  WARNING: RIOT_API_KEY not configured. Add it to your .env file.")
    else:
        print("✅ Riot API key configured")
    
    print(f"🚀 Starting TFT Analysis API server... (Set {trait_analysis.TFT_SET})")
    print("📍 Health check and endpoints: /")
    print("📊 Combined analysis: /analyze-all-riot-id?gameName=NAME&tagLine=TAG")
    print("📊 Trait analysis: /analyze-traits-riot-id?gameName=NAME&tagLine=TAG")
    print("📊 Item analysis: /analyze-items-riot-id?gameName=NAME&tagLine=TAG")
    print("📊 Units analysis: /analyze-units-riot-id?gameName=NAME&tagLine=TAG")
    
    # Use PORT environment variable for Render, fallback to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)