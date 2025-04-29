# Consultation Services Website

A Django-based website for consultation services with features like service listings, blog posts, and contact forms.

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
.\venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Create a .env file in the project root with the following variables:
```
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

The website will be available at http://127.0.0.1:8000/

## Features

- Home page with featured services and recent blog posts
- Services page with detailed service listings
- Blog page with articles and categories
- Contact page with a contact form
- Responsive design using Bootstrap 5
- Admin interface for managing content

## Project Structure

- `core/` - Main app with home, about, and contact pages
- `services/` - App for managing consultation services
- `blog/` - App for blog posts and categories
- `templates/` - HTML templates for all pages
- `static/` - Static files (CSS, JavaScript, images)
- `media/` - User-uploaded files 