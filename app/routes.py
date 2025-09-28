from flask import render_template, request, redirect, url_for, flash, jsonify

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