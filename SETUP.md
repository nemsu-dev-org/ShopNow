# 🚀 ShopNow Setup Guide

This guide will help you set up ShopNow on your local machine or production server.

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git
- A code editor (VS Code, PyCharm, etc.)

## 🔧 Environment Configuration

Create a `.env` file in the project root with the following variables:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DATABASE_URL=sqlite:///db.sqlite3
# For PostgreSQL: postgresql://user:password@localhost:5432/shopnow_db

# Email Configuration (for password reset and notifications)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Google OAuth (for social authentication)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Static Files
STATIC_URL=/static/
MEDIA_URL=/media/

# Security Settings
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True

# Payment Gateway (if using external payment)
STRIPE_PUBLIC_KEY=your-stripe-public-key
STRIPE_SECRET_KEY=your-stripe-secret-key

# Currency (optional): Philippine pesos per US dollar, used to show prices in PHP
USD_TO_PHP_RATE=59.41

# Production Settings
# DEBUG=False
# ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## 🔑 Generating a Secret Key

Generate a secure secret key for your Django application:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

## 📧 Email Setup

### Gmail Configuration
1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a new app password for "Mail"
3. Use the generated password in your `.env` file

### Alternative Email Providers
- **SendGrid**: Use SMTP with SendGrid credentials
- **Mailgun**: Use Mailgun SMTP settings
- **AWS SES**: Use AWS Simple Email Service

## 🌐 Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials:
   - Go to APIs & Services → Credentials
   - Create Credentials → OAuth 2.0 Client IDs
   - Set authorized redirect URIs:
     - `http://localhost:8000/accounts/google/login/callback/` (development)
     - `https://yourdomain.com/accounts/google/login/callback/` (production)
5. Copy Client ID and Client Secret to your `.env` file

## 🗄️ Database Setup

### SQLite (Default - Development)
No additional setup required. SQLite database will be created automatically.

### PostgreSQL (Production Recommended)
1. Install PostgreSQL
2. Create a database:
   ```sql
   CREATE DATABASE shopnow_db;
   CREATE USER shopnow_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE shopnow_db TO shopnow_user;
   ```
3. Update `DATABASE_URL` in your `.env` file:
   ```
   DATABASE_URL=postgresql://shopnow_user:your_password@localhost:5432/shopnow_db
   ```

## 🚀 Quick Start Commands

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/ShopNow.git
cd ShopNow

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file (copy from example above)

# 6. Navigate to src directory
cd src

# 7. Run migrations
python manage.py makemigrations
python manage.py migrate

# 8. Create superuser
python manage.py createsuperuser

# 9. Collect static files
python manage.py collectstatic

# 10. Run development server
python manage.py runserver
```

## 🔍 Verification Steps

After setup, verify everything is working:

1. **Access the site**: http://127.0.0.1:8000
2. **Check admin panel**: http://127.0.0.1:8000/admin
3. **Test user registration**: Try creating a new account
4. **Test email functionality**: Try password reset
5. **Test Google OAuth**: Try logging in with Google

## 🐛 Troubleshooting

### Common Issues

**1. Import Error: No module named 'django'**
```bash
# Solution: Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

**2. Database connection error**
```bash
# Solution: Check DATABASE_URL in .env file
# For SQLite, ensure the path is correct
```

**3. Static files not loading**
```bash
# Solution: Run collectstatic
python manage.py collectstatic
```

**4. Email not sending**
```bash
# Solution: Check email settings in .env
# Ensure EMAIL_HOST_PASSWORD is an app password, not regular password
```

**5. Google OAuth not working**
```bash
# Solution: Check redirect URIs in Google Cloud Console
# Ensure they match your domain exactly
```

### Debug Mode

For development, ensure `DEBUG=True` in your `.env` file. This will show detailed error messages.

## 🔒 Production Deployment

### Security Checklist
- [ ] Set `DEBUG=False`
- [ ] Use a strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use HTTPS
- [ ] Set up proper database
- [ ] Configure email settings
- [ ] Set up static file serving
- [ ] Enable CSRF protection

### Recommended Hosting Platforms
- **Heroku**: Easy deployment with PostgreSQL
- **DigitalOcean**: VPS with full control
- **AWS**: Scalable cloud infrastructure
- **Vercel**: Fast deployment with serverless

## 📞 Support

If you encounter issues:
1. Check the [main README.md](README.md)
2. Review Django documentation
3. Search existing issues
4. Create a new issue with detailed information

---

**Happy coding! 🚀**
