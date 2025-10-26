# SDO-Webinar-Evaluation-System 🚀

Evalsync is a comprehensive platform designed to simplify and enhance the management of webinars. It provides tools for creating, organizing, and delivering engaging online events, along with features for attendee registration, feedback collection, and performance analysis. It addresses the challenges of managing webinars efficiently, offering a centralized solution for all aspects of the webinar lifecycle.

## 🚀 Key Features

- **Webinar Creation & Management:** Easily create and manage webinar details, including title, description, date, time, venue, and banner.
- **Speaker Management:** Add and manage speakers associated with webinars, including their name, image, and email.
- **Attendee Registration:** Streamline the registration process for attendees, capturing essential information.
- **Questionnaires & Tests:** Create and manage questionnaires and tests to gather feedback and assess attendee understanding.
- **Comment Management:** Facilitate discussions and gather feedback through comment management features.
- **QR Code Generation:** Generate QR codes for easy access to webinar registration and information.
- **User Authentication & Authorization:** Secure access to the platform with robust authentication and authorization mechanisms.
- **Email Notifications:** Send automated email notifications for registration confirmation and reminders.
- **Asynchronous Task Execution:** Utilizes task queues for sending OTP emails, preventing delays in the user interface.
- **Cloudinary Integration:** Seamlessly store and manage images using Cloudinary cloud storage.
- **Supabase Integration:** Uses Supabase for backend services, including database and API management.

## 🛠️ Tech Stack

- **Frontend:**
  - HTML
  - CSS
  - JavaScript
- **Backend:**
  - Python
  - Django
- **Database:**
  - PostgreSQL (via Supabase)
- **Build Tools:**
  - pip
- **Cloud Storage:**
  - Cloudinary
- **Email Service:**
  - Resend
- **Other:**
  - QR code generation library
  - Supabase CLI

## 📦 Getting Started

### Prerequisites

- Python 3.x
- pip (Python package installer)
- Django
- Supabase CLI
- Resend API Key (set as environment variable `RESEND_API_KEY`)
- Cloudinary account and API keys (configured in Django settings)

### Installation

1.  Clone the repository:

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  Create a virtual environment:

    ```bash
    python -m venv venv
    ```

3.  Activate the virtual environment:

    -   On Windows:

        ```bash
        venv\Scripts\activate
        ```

    -   On macOS and Linux:

        ```bash
        source venv/bin/activate
        ```

4.  Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```
    **Note:** If you encounter an error reading `requirements.txt`, ensure the file is properly encoded (UTF-8) and not corrupted.

5.  Set up Supabase:

    -   Install the Supabase CLI: Follow the instructions on the Supabase website.
    -   Initialize Supabase:

        ```bash
        supabase init
        ```

    -   Start Supabase:

        ```bash
        supabase start
        ```

    -   Apply database migrations:

        ```bash
        supabase db push
        ```

6. Configure Django settings:

    - Set the `DJANGO_SETTINGS_MODULE` environment variable.
    - Configure database settings to connect to the Supabase PostgreSQL instance.
    - Configure Cloudinary settings with your Cloudinary API keys.
    - Configure Resend API key as an environment variable (`RESEND_API_KEY`).
    - Configure email settings for sending OTP emails (if not using Resend exclusively).

### Running Locally

1.  Apply Django migrations:

    ```bash
    python manage.py migrate
    ```

2.  Create a superuser:

    ```bash
    python manage.py createsuperuser
    ```

3.  Start the Django development server:

    ```bash
    python manage.py runserver
    ```

4.  Access the application in your web browser at `http://localhost:8000` (or the port specified in your Django settings).

## 📂 Project Structure

```
.
├── manage.py               # Django management script
├── login/                  # Login application
│   ├── models.py           # Data models for user profiles, trusted devices, and OTP
│   ├── task.py             # Asynchronous task for sending OTP emails
│   ├── email_service.py    # Function for sending emails using Resend
│   └── ...
├── webinar/                # Webinar application
│   ├── models.py           # Data models for webinars, speakers, and attendees
│   ├── views.py            # View functions for handling HTTP requests
│   ├── admin.py            # Django admin configuration
│   ├── urls.py             # URL patterns for the webinar app
│   └── ...
├── supabase/               # Supabase configuration
│   └── config.toml         # Configuration file for local Supabase environment
├── requirements.txt        # Python package dependencies
└── ...
```

## 📸 Screenshots

(Add screenshots of the application here to showcase its features and UI)

## 🤝 Contributing

We welcome contributions to Evalsync! To contribute:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and commit them with descriptive messages.
4.  Submit a pull request.

## 📝 License

This project is licensed under the [MIT License](LICENSE).

## 📬 Contact

For questions or inquiries, please contact: [Your Name/Organization] - [Your Email]

## 💖 Thanks

Thank you for your interest in Evalsync! We hope this platform helps you streamline your webinar management process.

This is written by [readme.ai](https://readme-generator-phi.vercel.app/).
