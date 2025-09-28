from flask import render_template, request, redirect, url_for, flash, jsonify
import time
import subprocess
import os
import threading
import sys


def register_routes(app, auth_service):
    @app.route('/')
    def index():
        """Home page"""
        user = auth_service.get_user_profile()
        return render_template('index.html', user=user)

    @app.route('/login')
    def login():
        """Login page with Auth0"""
        return render_template('login.html')
    
    @app.route('/auth/login')
    def auth_login():
        """Redirect to Auth0 login"""
        return auth_service.login()
    
    @app.route('/auth/passwordless', methods=['POST'])
    def passwordless_login():
        """Send passwordless login email"""
        email = request.form.get('email')
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        success = auth_service.passwordless_login(email)
        if success:
            return jsonify({'message': 'Check your email for the login link'})
        else:
            return jsonify({'error': 'Failed to send login email'}), 500
    
    @app.route('/callback')
    def callback():
        """Auth0 callback"""
        return auth_service.callback()
    
    @app.route('/logout')
    def logout():
        """Logout user"""
        return auth_service.logout()
    
    @app.route('/dashboard')
    @auth_service.requires_auth
    def dashboard():
        """User dashboard - requires authentication"""
        user = auth_service.get_user_profile()
        return render_template('dashboard.html', user=user)
    
    @app.route('/profile')
    @auth_service.requires_auth
    def profile():
        """User profile page"""
        user = auth_service.get_user_profile()
        return render_template('profile.html', user=user)

    @app.route('/about')
    def about():
        """About page"""
        user = auth_service.get_user_profile()
        return render_template('about.html', user=user)

    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        """Contact page"""
        user = auth_service.get_user_profile()
        
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            message = request.form.get('message')
            
            # Simple success message
            success_message = f"Thank you {name}! We received your message."
            return render_template('contact.html', message=success_message, user=user)
        
        return render_template('contact.html', user=user)

    @app.route('/dynamic_split')
    def dynamic_split():
        """Dynamic split page"""
        user = auth_service.get_user_profile()
        return render_template('dynamic_split.html', user=user)

    @app.route('/expenses_split')
    def expenses_split():
        """Link to the static expense splitter page"""
        user = auth_service.get_user_profile()
        return render_template('splitter.html', user=user)

    # Simple in-memory timers for demo (name -> start_ts)
    timers = {}
    # Accumulated totals (seconds)
    totals = {}
    # Currently recognized user (most recent)
    current_user = {'name': None, 'start': None}
    # background recognition process state
    recognize_proc = {'proc': None}
    recognize_thread = {'thread': None}

    def _reader_thread(proc):
        # read stdout lines and look for RECOG_RESULT tokens
        try:
            for raw in proc.stdout:
                line = raw.strip()
                if not line:
                    continue
                # parse token
                if line.startswith('RECOG_RESULT:'):
                    name = line.split(':', 1)[1].strip()
                    # start timer for first recognized person only
                    if name and name != 'Unknown' and current_user['name'] is None:
                        timers[name] = time.time()
                        current_user['name'] = name
                        current_user['start'] = timers[name]
        except Exception:
            pass
        finally:
            try:
                proc.stdout.close()
            except Exception:
                pass

    @app.route('/demo')
    def demo():
        """Demo page for the light-switch + facial recognition"""
        user = auth_service.get_user_profile()
        return render_template('demo.html', timers=timers, totals=totals, user=user)

    @app.route('/demo/recognize', methods=['POST'])
    def demo_recognize():
        """Start the facial recognition subprocess; when a known face is found, start that person's timer."""
        # Run the facial recognition script in single-exit mode. The script will print the recognized
        # person's name on stdout and exit. We call it with an explicit path so it finds its known/ folder.
        script_path = os.path.join(os.path.dirname(__file__), 'facial_recognition', 'realtime_recog.py')
        # legacy endpoint: run a single-shot recognition (keeps existing behavior)
        try:
            proc = subprocess.run(['python3', script_path, '--single-exit'], capture_output=True, text=True, timeout=300)
            out = proc.stdout.strip().splitlines()
            # look for the RECOG_RESULT:<name> token in stdout
            name = 'Unknown'
            for line in out:
                if line.startswith('RECOG_RESULT:'):
                    name = line.split(':', 1)[1].strip()
                    break
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

    @app.route('/demo/switch', methods=['POST'])
    def demo_switch():
        """Toggle the demo camera (light switch). When switched on, start background recognition.
        When switched off, stop background recognition and stop the current user's timer if any.
        """
        # if process is running -> stop it
        if recognize_proc['proc'] is not None and recognize_proc['proc'].poll() is None:
            try:
                recognize_proc['proc'].terminate()
            except Exception:
                try:
                    recognize_proc['proc'].kill()
                except Exception:
                    pass
            # wait briefly
            try:
                recognize_proc['proc'].wait(timeout=1)
            except Exception:
                pass
            recognize_proc['proc'] = None
            # if someone was being billed, stop them now
            if current_user['name']:
                name = current_user['name']
                if name in timers:
                    elapsed = time.time() - timers.pop(name)
                    totals[name] = totals.get(name, 0) + elapsed
                current_user['name'] = None
                current_user['start'] = None
            return jsonify({'status': 'ok', 'camera_on': False})

        # start background recognition process
        script_path = os.path.join(os.path.dirname(__file__), 'facial_recognition', 'realtime_recog.py')
        try:
            # launch subprocess and capture stdout to read tokens
            proc = subprocess.Popen([sys.executable, script_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            recognize_proc['proc'] = proc
            th = threading.Thread(target=_reader_thread, args=(proc,), daemon=True)
            recognize_thread['thread'] = th
            th.start()
            return jsonify({'status': 'ok', 'camera_on': True})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

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

    @app.route('/demo/clear_totals', methods=['POST'])
    def demo_clear_totals():
        """Clear accumulated totals for demo (in-memory)."""
        totals.clear()
        # also clear timers if desired (keep timers running as-is — only clearing totals)
        return jsonify({'status': 'ok'})
