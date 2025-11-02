# 🎓 Webinar Evaluation System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Django](https://img.shields.io/badge/Django-Framework-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue.svg)
![Supabase](https://img.shields.io/badge/Supabase-Backend-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

A comprehensive platform designed to simplify and enhance the management of webinars, providing tools for creating, organizing, and delivering engaging online events.

[Features](#-features) • [Tech Stack](#-tech-stack) • [Installation](#-installation) • [Usage](#-usage) • [Contributing](#-contributing)

</div>

---

## 📖 About

Evalsync is a powerful webinar management platform that addresses the challenges of managing webinars efficiently. It offers a centralized solution for all aspects of the webinar lifecycle, from creation and speaker management to attendee registration, feedback collection, and performance analysis.

## ✨ Features

### 🎯 Core Features

- **Webinar Creation & Management**
  - Create and manage comprehensive webinar details
  - Set title, description, date, time, venue, and custom banners
  - Organize and track all webinars from a single dashboard

- **Speaker Management**
  - Add and manage multiple speakers per webinar
  - Store speaker profiles with name, image, and contact information
  - Seamless speaker-webinar association

- **Attendee Registration**
  - Streamlined registration process for participants
  - Capture essential attendee information
  - Track registration status and attendance

- **Questionnaires & Tests**
  - Create custom questionnaires for feedback collection
  - Design tests to assess attendee understanding
  - Analyze responses and generate insights

- **Interactive Features**
  - Comment management system for discussions
  - Real-time feedback collection
  - QR code generation for easy registration access

### 🔐 Security & Authentication

- Robust user authentication and authorization
- Secure login system with OTP verification
- Trusted device management
- Role-based access control

### 📧 Communication

- Automated email notifications
- Registration confirmation emails
- Webinar reminders
- Asynchronous email delivery using task queues

### ☁️ Cloud Integration

- **Cloudinary** integration for image storage and management
- **Supabase** backend for database and API services
- Scalable cloud infrastructure

## 🛠️ Tech Stack

### Frontend
- HTML5
- CSS3
- JavaScript

### Backend
- **Python 3.x**
- **Django Framework**

### Database
- **PostgreSQL** (via Supabase)

### Cloud Services
- **Supabase** - Backend services and database
- **Cloudinary** - Image storage and CDN
- **Resend** - Email delivery service

### Tools & Libraries
- pip - Package management
- QR code generation library
- Supabase CLI
- Django ORM

## 📦 Installation

### Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.x
- pip (Python package installer)
- Django
- Supabase CLI
- Resend API Key
- Cloudinary account and API keys

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/noireflakes/SDO-Webinar-Evaluation-System.git
   cd SDO-Webinar-Evaluation-System
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   
   On Windows:
   ```bash
   venv\Scripts\activate
   ```
   
   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   > **Note:** If you encounter encoding errors, ensure `requirements.txt` is UTF-8 encoded.

5. **Set up Supabase**
   
   Install Supabase CLI (follow [official instructions](https://supabase.com/docs/guides/cli))
   ```bash
   supabase init
   supabase start
   supabase db push
   ```

6. **Configure environment variables**
   
   Set the following environment variables:
   ```bash
   export DJANGO_SETTINGS_MODULE=your_project.settings
   export RESEND_API_KEY=your_resend_api_key
   ```
   
   Configure in Django settings:
   - Database connection to Supabase PostgreSQL
   - Cloudinary API keys
   - Email service settings

7. **Apply Django migrations**
   ```bash
   python manage.py migrate
   ```

8. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

9. **Start the development server**
   ```bash
   python manage.py runserver
   ```

10. **Access the application**
    
    Open your browser and navigate to: `http://localhost:8000`

## 📁 Project Structure

```
.
├── manage.py                 # Django management script
├── login/                    # Login application
│   ├── models.py            # User profiles, trusted devices, OTP models
│   ├── task.py              # Asynchronous OTP email tasks
│   ├── email_service.py     # Email sending functionality
│   └── ...
├── webinar/                  # Webinar application
│   ├── models.py            # Webinar, speaker, attendee models
│   ├── views.py             # HTTP request handlers
│   ├── admin.py             # Django admin configuration
│   ├── urls.py              # URL routing
│   └── ...
├── supabase/                 # Supabase configuration
│   └── config.toml          # Local environment config
├── requirements.txt          # Python dependencies
└── ...
```

## 🚀 Usage

1. **Admin Panel**: Access the Django admin at `/admin` using your superuser credentials
2. **Create Webinar**: Navigate to the webinar creation page and fill in the details
3. **Add Speakers**: Associate speakers with your webinar
4. **Generate QR Codes**: Create QR codes for easy attendee registration
5. **Manage Registrations**: Track and manage attendee registrations
6. **Collect Feedback**: Create questionnaires and tests for evaluation
7. **Analyze Results**: View feedback and generate performance reports

## 🤝 Contributing

We welcome contributions to Evalsync! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/YourFeatureName
   ```
3. **Make your changes**
4. **Commit with descriptive messages**
   ```bash
   git commit -m "Add: Description of your feature"
   ```
5. **Push to your branch**
   ```bash
   git push origin feature/YourFeatureName
   ```
6. **Submit a Pull Request**

### Contribution Guidelines

- Follow PEP 8 style guide for Python code
- Write clear commit messages
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR

## 📄 License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.

## 📧 Contact

For questions, suggestions, or support:

- **GitHub Issues**: [Create an issue](https://github.com/noireflakes/SDO-Webinar-Evaluation-System/issues)
- **Repository**: [SDO-Webinar-Evaluation-System](https://github.com/noireflakes/SDO-Webinar-Evaluation-System)

## 🙏 Acknowledgments

- Django Framework
- Supabase
- Cloudinary
- Resend
- All contributors and supporters

---

