# My Web App

A modern Flask web application with a clean, responsive design.

## Features

- **Modern UI**: Bootstrap-based responsive design
- **Database Integration**: SQLAlchemy with SQLite
- **Form Handling**: WTForms for secure form processing
- **Template Engine**: Jinja2 templates with inheritance
- **Static Files**: Organized CSS, JavaScript, and images
- **Contact Form**: Working contact form with validation
- **Sample Data**: Pre-populated with sample users and posts

## Project Structure

```
my_webapp/
│
├── app/                         # Main application package
│   ├── static/                  # Static files (CSS, JS, images)
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/
│   │   │   └── script.js
│   │   └── img/
│   │       └── logo.png
│   │
│   ├── templates/              # HTML pages
│   │   ├── base.html           # Base layout
│   │   ├── index.html          # Home page
│   │   ├── about.html          # About page
│   │   └── contact.html        # Contact page
│   │
│   ├── routes.py               # Route handlers (views)
│   ├── models.py               # Database models
│   ├── forms.py                # Form definitions
│   └── __init__.py             # App factory
│
├── instance/                   # Database and instance files
│   └── app.db                  # SQLite database file
│
├── config.py                   # Configuration settings
├── run.py                      # Application entry point
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Installation

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd my_webapp
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python run.py init-db
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:5000`

## Configuration

The application uses environment variables for configuration:

- `FLASK_ENV`: Set to 'development', 'production', or 'testing'
- `SECRET_KEY`: Secret key for session management
- `DATABASE_URL`: Database connection string
- `PORT`: Port number (default: 5000)

## Usage

### Pages

- **Home** (`/`): Welcome page with recent posts
- **About** (`/about`): Information about the application
- **Contact** (`/contact`): Contact form

### Database Models

- **User**: User accounts with username and email
- **Post**: Blog posts with title, content, and author
- **ContactMessage**: Contact form submissions

### Forms

- **ContactForm**: Name, email, and message fields
- **PostForm**: Title and content for creating posts
- **UserForm**: Username and email for user registration

## Development

### Adding New Routes

1. Add route functions to `app/routes.py`
2. Create corresponding templates in `app/templates/`
3. Update navigation in `base.html` if needed

### Adding New Models

1. Define models in `app/models.py`
2. Import in `run.py` for shell context
3. Run database migrations if using Flask-Migrate

### Styling

- Main styles: `app/static/css/style.css`
- Uses Bootstrap 5 for responsive design
- Custom animations and effects included

## Deployment

For production deployment:

1. Set `FLASK_ENV=production`
2. Use a production WSGI server like Gunicorn
3. Set up a proper database (PostgreSQL recommended)
4. Configure environment variables securely
5. Use a reverse proxy like Nginx

## License

This project is open source and available under the [MIT License](LICENSE).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For questions or support, please contact us through the contact form on the website.