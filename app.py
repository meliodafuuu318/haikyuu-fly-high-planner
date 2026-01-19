from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os

# Import the GachaSimulator from your main.py
# Make sure main.py is in the same directory
from main import GachaSimulator

app = Flask(__name__, static_folder='.')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    try:
        data = request.json
        
        # Extract parameters
        diamonds = data['diamonds']
        ur_tickets = data['ur_tickets']
        sp_tickets = data['sp_tickets']
        ur_pity = data['ur_pity']
        sp_pity = data['sp_pity']
        free_ur = data['free_ur']
        free_sp = data['free_sp']
        daily_income = data['daily_income']
        num_sims = data['num_sims']
        
        # Convert targeted banners to the format expected by the simulator
        targeted_banners = [(b['name'], b['copies']) for b in data['targeted_banners']]
        
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
            if 'start_date' in banner_stats and banner_stats['start_date']:
                banner_stats['start_date'] = banner_stats['start_date'].strftime('%Y-%m-%d')
            if 'end_date' in banner_stats and banner_stats['end_date']:
                banner_stats['end_date'] = banner_stats['end_date'].strftime('%Y-%m-%d')
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)