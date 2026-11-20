# BudgetAI — Club Budget and Expense Tracker

BudgetAI is a Django web application for student clubs and campus societies to manage club membership, expense requests, approvals, receipts, and financial records.

## Current capabilities

- Email/password account registration and login.
- Create and manage more than one club per account.
- Club membership with President, Treasurer, and Member roles.
- Submit expense requests with descriptions, amounts, categories, dates, and receipt files.
- Review requests and record approved expenses as club transactions.
- Record club income and view transaction history.
- Configure a treasurer approval limit as the club President.
- View in-app notifications and generate financial reports as PDFs.

AI receipt upload and extraction suggestions are available as a draft workflow. The draft-to-final expense confirmation step is still to be completed.

## Technology

- Python 3.13
- Django 5.2
- SQLite for local development, or PostgreSQL through `DATABASE_URL`
- WeasyPrint for report PDF generation
- OpenAI Python SDK configured for an OpenAI-compatible DeepSeek endpoint

## Clone and run locally

The commands below use PowerShell on Windows. Run them from the folder where you keep your projects.

1. Clone the GitHub repository and enter its folder:

   ```powershell
   git clone https://github.com/CHUNG-WEI-YONG/airost_project.git
   cd airost_project
   ```

2. Create and activate a virtual environment:

   ```powershell
   py -3.13 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt instead:

   ```bat
   .venv\Scripts\activate.bat
   ```

3. Install Python dependencies:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. Create your local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

   Open `.env` and configure email and AI values. `DATABASE_URL` can remain blank to use local SQLite. To connect to Neon PostgreSQL, set it to your Neon connection URL. To use cloud file storage, enable it and provide the S3-compatible values described below. Never commit `.env` or share its credentials.

5. Create database tables and start Django:

   ```powershell
   python manage.py migrate
   python manage.py runserver
   ```

6. Open <http://127.0.0.1:8000/> and register an account. Creating a club makes that account its President.

To create a Django admin account for `/admin/`, run this separately:

```powershell
python manage.py createsuperuser
```

## Environment variables

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Optional PostgreSQL connection URL. Leave blank for local SQLite. |
| `EMAIL_HOST` | SMTP server hostname. |
| `EMAIL_PORT` | SMTP port; this project defaults to `587`. |
| `EMAIL_USE_TLS` | Enable SMTP TLS. |
| `EMAIL_USE_SSL` | Enable SMTP SSL; do not enable TLS and SSL together. |
| `EMAIL_HOST_USER` | SMTP account username. |
| `EMAIL_HOST_PASSWORD` | SMTP password or provider app password. |
| `DEFAULT_FROM_EMAIL` | Sender address shown on application email. |
| `OPENAI_API_KEY` | DeepSeek API key used through the OpenAI-compatible Python SDK. |
| `OPENAI_BASE_URL` | Set to `https://api.deepseek.com` when using DeepSeek. |
| `OPENAI_RECEIPT_MODEL` | Vision-capable model name, currently `deepseek-flash`. |
| `SECRET_KEY` | Django signing key; use a private generated value in deployment. |
| `DEBUG` | Django debug mode; set to `False` in deployment. |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames. |
| `USE_CLOUD_STORAGE` | Set to `True` to use the configured S3-compatible storage backend. |
| `AWS_ENDPOINT_URL_S3` | S3-compatible storage endpoint. |
| `AWS_ACCESS_KEY_ID` | S3-compatible storage access key. |
| `AWS_SECRET_ACCESS_KEY` | S3-compatible storage secret key. |
| `AWS_REGION` | S3-compatible storage region. |
| `AWS_STORAGE_BUCKET_NAME` | S3-compatible storage bucket name. |

When SMTP credentials are absent, local email uses Django's console backend. Add working SMTP credentials to send real email. For Gmail, use an App Password where supported, not your normal account password. See [Google's App Password guidance](https://support.google.com/mail/answer/185833).

On Windows, WeasyPrint PDF generation may also require native Pango libraries. If PDF generation fails with a missing DLL/library error, follow [the WeasyPrint Windows installation instructions](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation).

## Cloud persistence status

### PostgreSQL

`settings.py` uses `DATABASE_URL` when it is set and otherwise uses the local `db.sqlite3`. For deployment, add `DATABASE_URL` to the hosting service's environment variables and run `python manage.py migrate` against that database. The local `.env` file is not automatically available to a deployed service.

### Receipts and PDF files

An S3-compatible cloud file-storage backend is configured conditionally. Set `USE_CLOUD_STORAGE=True` and supply all five `AWS_*` values above to enable it. If disabled, files use local `MEDIA_ROOT` storage and will not persist through a redeploy. Existing local uploads must be copied to cloud storage separately.

Test uploads and downloads in the deployed environment before relying on cloud storage for receipt or report retention.

## Project layout

```text
airost_project/
├── account/       # Custom user model, registration, login, and account pages
├── clubs/         # Clubs, memberships, roles, and club pages
├── finance/       # Expense requests, transactions, notifications, reports
├── config/        # Django settings and root URL configuration
├── templates/     # Shared templates
├── static/        # Project-wide static files
├── manage.py
├── requirements.txt
├── .env.example   # Safe template for local environment variables
└── .gitignore
```

Each Django app also contains its own templates and static files.

## Before deployment

- Set a fresh `SECRET_KEY` through environment-based Django settings; the current settings file contains a development key.
- Set `DEBUG=False` and configure `ALLOWED_HOSTS` for the deployed domain.
- Configure a persistent PostgreSQL database and private cloud storage for receipts and PDFs.
- Add all required environment variables in the hosting dashboard; never upload `.env`.
- Configure static-file serving and verify role-based access to club data and receipt files.
- Rotate any credentials that were previously committed or shared. Removing a file from the latest Git commit does not erase it from earlier Git history.

## License

No license has been added yet. Ask the project owner before reusing this project outside its intended academic use.

