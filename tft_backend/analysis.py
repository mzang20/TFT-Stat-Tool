from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import sys
import os

# Import your analysis function
from analysis import run_analysis

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('tft_api.log')
    ]
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
            logger.warning("Request missing PUUID")
            return jsonify({'error': 'PUUID is required'}), 400
        
        puuid = data['puuid'].strip()
        
        if not puuid:
            logger.warning("Empty PUUID provided")
            return jsonify({'error': 'PUUID cannot be empty'}), 400
        
        # Basic PUUID validation
        if len(puuid) < 20:
            logger.warning(f"Invalid PUUID format: {puuid[:8]}...")
            return jsonify({'error': 'Invalid PUUID format - PUUIDs should be longer than 20 characters'}), 400
        
        logger.info(f"Starting analysis for PUUID: {puuid[:8]}...")
        
        # Run the analysis using your function
        top_traits, bottom_traits = run_analysis(puuid)
        
        # Validate results
        if not top_traits and not bottom_traits:
            logger.warning(f"No traits returned for {puuid[:8]}")
            return jsonify({'error': 'No trait data found for this player'}), 404
        
        # Return the results
        result = {
            'top_traits': top_traits,
            'bottom_traits': bottom_traits,
            'puuid': puuid[:8] + '...',  # Return partial PUUID for confirmation
            'message': 'Analysis completed successfully',
            'stats': {
                'top_traits_count': len(top_traits),
                'bottom_traits_count': len(bottom_traits),
                'total_traits_analyzed': len(top_traits) + len(bottom_traits)
            }
        }
        
        logger.info(f"Analysis completed successfully for {puuid[:8]} - {len(top_traits)} top traits, {len(bottom_traits)} bottom traits")
        return jsonify(result), 200
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Analysis failed for {puuid[:8] if 'puuid' in locals() else 'unknown'}: {error_message}")
        
        # Return appropriate error messages based on the error type
        if "API key" in error_message or "RIOT_API_KEY" in error_message:
            return jsonify({
                'error': 'API configuration error - please check server configuration',
                'details': 'Riot API key not found or invalid'
            }), 500
        elif "PUUID not found" in error_message or "no matches available" in error_message:
            return jsonify({
                'error': 'Player not found or no matches available',
                'details': 'This PUUID may not exist or has no recent TFT matches'
            }), 404
        elif "Rate limited" in error_message or "429" in error_message:
            return jsonify({
                'error': 'Rate limited by Riot API',
                'details': 'Too many requests. Please try again in a few minutes.'
            }), 429
        elif "Insufficient" in error_message:
            return jsonify({
                'error': 'Not enough Set 13 matches found',
                'details': 'Play more ranked TFT games in Set 13 and try again. At least 3 matches are needed for analysis.'
            }), 400
        elif "Network error" in error_message or "timeout" in error_message.lower():
            return jsonify({
                'error': 'Network connectivity issue',
                'details': 'Unable to connect to Riot API. Please check your connection and try again.'
            }), 503
        elif "No traits found" in error_message:
            return jsonify({
                'error': 'Insufficient trait data',
                'details': 'Not enough trait appearances in your matches for meaningful analysis'
            }), 400
        else:
            return jsonify({
                'error': 'Analysis failed',
                'details': error_message
            }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    try:
        # Check if API key is configured
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("RIOT_API_KEY")
        
        health_status = {
            'status': 'healthy',
            'message': 'TFT Analysis API is running',
            'api_key_configured': bool(api_key),
            'version': '1.0.0',
            'endpoints': {
                'analyze': '/api/analyze (POST)',
                'health': '/api/health (GET)'
            }
        }
        
        if not api_key:
            health_status['warnings'] = ['RIOT_API_KEY not configured']
            
        return jsonify(health_status), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/analyze', methods=['GET'])
def analyze_player_get():
    """
    Alternative GET endpoint for testing
    Usage: /analyze?puuid=your_puuid_here
    """
    try:
        puuid = request.args.get('puuid')
        
        if not puuid:
            return jsonify({'error': 'PUUID parameter is required'}), 400
        
        # Use the same logic as POST endpoint
        logger.info(f"GET request - Starting analysis for PUUID: {puuid[:8]}...")
        
        top_traits, bottom_traits = run_analysis(puuid)
        
        result = {
            'top_traits': top_traits,
            'bottom_traits': bottom_traits,
            'puuid': puuid[:8] + '...',
            'message': 'Analysis completed successfully (GET endpoint)'
        }
        
        logger.info(f"GET analysis completed for {puuid[:8]}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"GET analysis failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            'POST /api/analyze',
            'GET /api/health', 
            'GET /analyze'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'Something went wrong on the server'
    }), 500

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'error': 'Method not allowed',
        'message': 'Check the HTTP method and endpoint'
    }), 405

if __name__ == '__main__':
    # Startup checks
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("RIOT_API_KEY")
        
        if not api_key:
            logger.warning("RIOT_API_KEY not found in environment variables")
            print("WARNING: RIOT_API_KEY not configured. Add it to your .env file.")
            print("Create a .env file with: RIOT_API_KEY=your_api_key_here")
        else:
            logger.info("API key configured successfully")
            print("Riot API key configured")
        
        # Test import of analysis function
        logger.info("Analysis function imported successfully")
        print("Analysis module loaded")
        
        print(f"\nStarting TFT Analysis API server...")
        print(f"Health check: http://localhost:5000/api/health")
        print(f"Analysis endpoint: POST http://localhost:5000/api/analyze")
        print(f"Test endpoint: GET http://localhost:5000/analyze?puuid=YOUR_PUUID")
        
    except ImportError as e:
        logger.error(f"Failed to import analysis module: {e}")
        print(f"Error importing analysis.py: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Startup error: {e}")
        print(f"Startup error: {e}")
        sys.exit(1)
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)