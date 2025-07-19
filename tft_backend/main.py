import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from analysis import run_analysis
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
MASS_REGION = "americas"

# Import and override the TFT_SET from analysis module
import analysis
analysis.TFT_SET = 14  # Force Set 14

app = Flask(__name__)
CORS(app)

def get_puuid_from_riot_id(game_name, tag_line):
    """Get PUUID from Riot ID (game name + tag line)"""
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
        "tft_set": analysis.TFT_SET,
        "api_key_configured": bool(API_KEY),
        "endpoints": {
            "analyze_by_puuid": "/analyze?puuid=YOUR_PUUID",
            "analyze_by_riot_id": "/analyze-riot-id?gameName=GAME_NAME&tagLine=TAG_LINE"
        },
        "examples": {
            "riot_id": "/analyze-riot-id?gameName=WukLamatHater&tagLine=Monke",
            "puuid": "/analyze?puuid=oeUTUlTvQIJUxqO955b0viyfcv_-2zvQgTSdhgFJg1nTNJpPSMgtu65dKhC780TONNCU91gxAdNjdQ"
        }
    })

@app.route('/analyze-riot-id')
def analyze_by_riot_id():
    """
    Analyze a player's TFT trait performance using Riot ID
    Usage: GET /analyze-riot-id?gameName=GAME_NAME&tagLine=TAG_LINE
    """
    try:
        game_name = request.args.get('gameName')
        tag_line = request.args.get('tagLine')
        
        if not game_name or not tag_line:
            return jsonify({'error': 'Both gameName and tagLine parameters are required'}), 400
        
        game_name = game_name.strip()
        tag_line = tag_line.strip()
        
        if not game_name or not tag_line:
            return jsonify({'error': 'Game name and tag line cannot be empty'}), 400
        
        print(f"Starting Set {analysis.TFT_SET} analysis for Riot ID: {game_name}#{tag_line}")
        
        # First, get the PUUID from Riot ID
        puuid = get_puuid_from_riot_id(game_name, tag_line)
        
        # Then run the analysis with the PUUID
        top_traits, bottom_traits = run_analysis(puuid)
        
        # Return the results
        result = {
            'top_traits': top_traits,
            'bottom_traits': bottom_traits,
            'riot_id': f"{game_name}#{tag_line}",
            'puuid': puuid[:8] + '...',
            'tft_set': analysis.TFT_SET,
            'message': f'Set {analysis.TFT_SET} analysis completed successfully'
        }
        
        print(f"Set {analysis.TFT_SET} analysis completed successfully for {game_name}#{tag_line}")
        return jsonify(result), 200
        
    except Exception as e:
        error_message = str(e)
        print(f"Analysis failed: {error_message}")
        
        # Return appropriate error messages
        if "API key" in error_message:
            return jsonify({'error': 'API configuration error'}), 500
        elif "Riot ID not found" in error_message:
            return jsonify({'error': 'Riot ID not found - check your game name and tag line'}), 404
        elif "Rate limited" in error_message:
            return jsonify({'error': 'Rate limited by Riot API. Please try again in a few minutes.'}), 429
        elif "Insufficient" in error_message:
            return jsonify({'error': f'Not enough Set {analysis.TFT_SET} matches found for analysis. Play more ranked games and try again.'}), 400
        elif "Network error" in error_message or "timeout" in error_message.lower():
            return jsonify({'error': 'Network error. Please check your connection and try again.'}), 503
        else:
            return jsonify({'error': f'Analysis failed: {error_message}'}), 500

@app.route('/analyze')
def analyze():
    """
    Analyze a player's TFT trait performance using PUUID
    Usage: GET /analyze?puuid=PLAYER_PUUID
    """
    puuid = request.args.get('puuid')
    if not puuid:
        return jsonify({"error": "Missing PUUID"}), 400
    
    try:
        top, bot = run_analysis(puuid)
        return jsonify({
            "top_traits": top,
            "bottom_traits": bot,
            "puuid": puuid[:8] + '...',
            "tft_set": analysis.TFT_SET,
            "message": f"Set {analysis.TFT_SET} analysis completed successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Check configuration on startup
    if not API_KEY:
        print("⚠️  WARNING: RIOT_API_KEY not configured. Add it to your .env file.")
    else:
        print("✅ Riot API key configured")
    
    print(f"🚀 Starting TFT Analysis API server... (Set {analysis.TFT_SET})")
    print("📍 Health check and endpoints: /")
    print("📊 Riot ID endpoint: /analyze-riot-id?gameName=NAME&tagLine=TAG")
    print("📊 PUUID endpoint: /analyze?puuid=PUUID")
    
    # Use PORT environment variable for Render, fallback to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)