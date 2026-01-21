from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import sys
import os

# Import the GachaSimulator from your main.py
from main import GachaSimulator

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve files from the assets directory"""
    try:
        assets_path = os.path.join(os.getcwd(), 'assets')
        print(f"Attempting to serve: {filename}")
        print(f"From path: {assets_path}")
        print(f"Full path: {os.path.join(assets_path, filename)}")
        print(f"File exists: {os.path.exists(os.path.join(assets_path, filename))}")
        return send_from_directory(assets_path, filename)
    except Exception as e:
        print(f"Error serving asset {filename}: {str(e)}")
        return str(e), 404

@app.route('/simulate', methods=['POST'])
def simulate():
    try:
        data = request.json
        
        diamonds = data.get('diamonds', 0)
        ur_tickets = data.get('ur_tickets', 0)
        sp_tickets = data.get('sp_tickets', 0)
        ur_pity = data.get('ur_pity', 0)
        sp_pity = data.get('sp_pity', 0)
        free_ur = data.get('free_ur', 0)
        free_sp = data.get('free_sp', 0)
        daily_income = data.get('daily_income', 0)
        num_sims = data.get('num_sims', 10000)
        
        # Convert targeted banners to the format expected by the simulator
        targeted_banners = [(b['name'], b['copies']) for b in data.get('targeted_banners', [])]
        
        # Create simulator and run
        sim = GachaSimulator()
        results = sim.run_monte_carlo(
            diamonds, 
            ur_tickets, 
            sp_tickets, 
            ur_pity, 
            sp_pity,
            free_ur, 
            free_sp, 
            targeted_banners, 
            daily_income, 
            num_sims
        )
        
        # Convert datetime objects to strings for JSON serialization
        for banner_name, banner_stats in results['banner_statistics'].items():
            if banner_stats.get('start_date'):
                banner_stats['start_date'] = banner_stats['start_date'].strftime('%Y-%m-%d')
            if banner_stats.get('end_date'):
                banner_stats['end_date'] = banner_stats['end_date'].strftime('%Y-%m-%d')
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)