from flask import Flask, request, jsonify
from flask_cors import CORS
from analysis import run_analysis

app = Flask(__name__)
CORS(app)

@app.route('/analyze')
def analyze():
    puuid = request.args.get('puuid')
    if not puuid:
        return jsonify({"error": "Missing PUUID"}), 400
    try:
        top, bot = run_analysis(puuid)
        return jsonify({
            "top_traits": top,
            "bottom_traits": bot
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()
