from flask import render_template, request

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