from flask import render_template, request, jsonify
import time
import subprocess
import os

def register_routes(app):
    @app.route('/')
    def index():
        """Home page"""
        return render_template('index.html')

    @app.route('/about')
    def about():
        """About page"""
        return render_template('about.html')

    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        """Contact page"""
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            message = request.form.get('message')
            
            # Simple success message
            success_message = f"Thank you {name}! We received your message."
            return render_template('contact.html', message=success_message)
        
        return render_template('contact.html')

    @app.route('/dynamic_split')
    def dynamic_split():
        """Dynamic split page"""
        return render_template('dynamic_split.html')

    # Simple in-memory timers for demo (name -> start_ts)
    timers = {}
    # Accumulated totals (seconds)
    totals = {}
    # Currently recognized user (most recent)
    current_user = {'name': None, 'start': None}

    @app.route('/demo')
    def demo():
        """Demo page for the light-switch + facial recognition"""
        return render_template('demo.html', timers=timers, totals=totals)

    @app.route('/demo/recognize', methods=['POST'])
    def demo_recognize():
        """Start the facial recognition subprocess; when a known face is found, start that person's timer."""
        # Run the facial recognition script in single-exit mode. The script will print the recognized
        # person's name on stdout and exit. We call it with an explicit path so it finds its known/ folder.
        script_path = os.path.join(os.path.dirname(__file__), 'facial_recognition', 'realtime_recog.py')
        try:
            proc = subprocess.run(['python3', script_path, '--single-exit'], capture_output=True, text=True, timeout=300)
            out = proc.stdout.strip().splitlines()
            name = out[-1] if out else 'Unknown'
        except subprocess.TimeoutExpired:
            return jsonify({'status': 'error', 'message': 'Recognition timed out'}), 504
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

        if name and name != 'Unknown':
            timers[name] = time.time()
            current_user['name'] = name
            current_user['start'] = timers[name]

        return jsonify({'status': 'ok', 'name': name})

    @app.route('/demo/stop', methods=['POST'])
    def demo_stop():
        data = request.get_json() or {}
        name = data.get('name')
        if not name or name not in timers:
            return jsonify({'status': 'error', 'message': 'No active timer for that name'}), 400
        elapsed = time.time() - timers.pop(name)
        totals[name] = totals.get(name, 0) + elapsed
        # if the stopped name is currently recognized/being billed, clear current_user so UI stops counting
        if current_user.get('name') == name:
            current_user['name'] = None
            current_user['start'] = None
        return jsonify({'status': 'ok', 'elapsed': elapsed, 'total': totals[name]})

    @app.route('/demo/status')
    def demo_status():
        # return JSON snapshot of timers (with elapsed if running) and totals
        now = time.time()
        snapshot = { 'timers': {}, 'totals': {} }
        for name, start in timers.items():
            snapshot['timers'][name] = now - start
        for name, sec in totals.items():
            snapshot['totals'][name] = sec
        # include current_user info
        snapshot['current'] = None
        if current_user['name']:
            snapshot['current'] = { 'name': current_user['name'], 'elapsed': now - current_user['start'] }
        return jsonify(snapshot)