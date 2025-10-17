# 🧾 Smart Invoice Scanner

An intelligent invoice processing system that uses Google's Gemini AI to extract and manage invoice data automatically.

## ✨ Features

- 🔐 **Secure Authentication** - User login with encrypted API key storage
- 🤖 **AI-Powered Extraction** - Automatic invoice data extraction using Gemini AI
- 📊 **Dashboard** - View and manage all invoices in one place
- ✏️ **Edit & Verify** - Review and correct extracted data
- 📥 **Excel Export** - Export invoices to Excel format
- 🔒 **Enterprise Security** - AES-256 encryption, rate limiting, CSRF protection

## 🏗️ Architecture

- **Backend**: Flask (Python)
- **Database**: SQLite (default) / PostgreSQL (production)
- **AI Engine**: Google Gemini API
- **Security**: Fernet encryption (AES-256), PBKDF2 key derivation

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/invoice-scanner.git
   cd invoice-scanner
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env and add your credentials
   # Generate SECRET_KEY: python -c "import secrets; print(secrets.token_hex(32))"
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open browser: `http://localhost:5000`
   - Login with your configured admin credentials
   - Enter your Gemini API key in settings

## 📁 Project Structure

```
invoice-scanner/
├── app/
│   ├── models/          # Database models
│   ├── routes/          # Application routes
│   ├── static/          # CSS and uploads
│   ├── templates/       # HTML templates
│   └── utils/           # Helper functions
├── instance/            # Database files (not in git)
├── .env.example         # Environment template
├── .gitignore          # Git ignore rules
├── app.py              # Application entry point
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## 🔒 Security Features

- **Encryption at Rest**: API keys encrypted with AES-256
- **Key Derivation**: PBKDF2-HMAC-SHA256 (100,000 iterations)
- **Rate Limiting**: Prevents brute force attacks
- **Input Validation**: XSS and SQL injection prevention
- **Secure Sessions**: HTTPOnly, Secure, SameSite cookies
- **Security Headers**: HSTS, CSP, X-Frame-Options

See [SECURITY_ARCHITECTURE.txt](SECURITY_ARCHITECTURE.txt) for detailed security design.

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Flask secret key | Yes |
| `ADMIN_EMAIL` | Admin login email | Yes |
| `ADMIN_PASSWORD` | Admin password | Yes |
| `DATABASE_URL` | Database connection string | No (defaults to SQLite) |

### Database Options

**SQLite (Development)**
```bash
DATABASE_URL=sqlite:///invoices.db
```

**PostgreSQL (Production)**
```bash
DATABASE_URL=postgresql://user:password@localhost/dbname
```

## 📊 Usage

1. **Login** - Use your admin credentials
2. **Add API Key** - Go to Settings and add your Gemini API key
3. **Upload Invoice** - Upload PDF, JPG, or PNG invoice
4. **Review Data** - AI extracts data automatically
5. **Edit if Needed** - Correct any extraction errors
6. **Export** - Download as Excel or manage in dashboard

## 🛠️ Development

### Running Tests
```bash
# Add your test commands here
pytest
```

### Database Migration
```bash
# Initialize database
python init_db.py
```

## 🚢 Deployment

### Heroku
```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:mini
git push heroku main
```

### Railway
```bash
railway init
railway add postgresql
railway up
```

### Docker (Coming Soon)
```bash
docker build -t invoice-scanner .
docker run -p 5000:5000 invoice-scanner
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please open an issue on GitHub.

## ⚠️ Important Notes

- **API Keys**: Users must provide their own Gemini API keys
- **Single User**: Designed for single-user deployment
- **Security**: Never commit `.env` file or database files
- **Production**: Use PostgreSQL and enable HTTPS in production

## 🙏 Acknowledgments

- Google Gemini AI for invoice extraction
- Flask framework and community
- All contributors and users

---

Made with ❤️ for efficient invoice management
