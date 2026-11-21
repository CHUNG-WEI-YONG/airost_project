# BudgetAI — Club Budget and Expense Tracker

BudgetAI is a Django website for student clubs and campus societies. It gives each club a private finance workspace where members submit expenses, club officers review them, and approved money movements are kept in a shared ledger.

## What the website does

- **Accounts and clubs:** Users register and sign in. A user can belong to several clubs and create clubs; the creator becomes that club’s President.
- **Club roles:** Each club assigns a President, Treasurer, and Members. Server-side views check club membership and role before allowing sensitive actions.
- **Expense requests:** Members submit a title, explanation, amount, purchase date, category, and receipt. They can follow the request status and cancel a pending request where permitted.
- **Review and limits:** Presidents and Treasurers review pending requests. The President sets the Treasurer’s approval limit. An approved request is recorded as an expense transaction.
- **Income and transaction history:** Authorized club officers can record income and review the club ledger, including money in and money out.
- **Notifications and email:** The site creates in-app notifications and sends email through Resend when credentials and an approved sender are configured.
- **Reports:** Club officers can view a date-range financial summary and export it as a PDF. Reports summarize income, expenses, approved requests, categories, and spending by member.
- **Receipt reading with AI:** A member can upload a receipt draft. The AI suggests merchant, amount, currency, and date; the member reviews and edits the values before submitting an actual expense request. AI output does not approve a request.
- **Finance assistant:** The chatbot answers questions about the current club’s records, declines unrelated questions, and stores each user’s chat history privately per club. Members’ answers are limited to the requests and transactions they are allowed to see.

AI features need a compatible API key and may incur provider charges. Without AI credentials, the rest of the site can still be used, but receipt reading and chat will return an unavailable message.

## Technology

- Python 3.13 and Django 5.2
- SQLite for local development, PostgreSQL when `DATABASE_URL` is configured
- Django templates, HTML, CSS, and a small amount of JavaScript
- Resend through django-anymail for email
- An OpenAI-compatible API endpoint (configured here for DeepSeek) for receipt reading and chat
- Optional S3-compatible storage for receipts and generated reports
- WeasyPrint for PDF reports
- WhiteNoise for serving collected static files in deployment

## Run locally on Windows

Open PowerShell in the folder where you keep your projects.

1. Clone the repository:

   ```powershell
   git clone https://github.com/CHUNG-WEI-YONG/airost_project.git
   cd airost_project
   ```

2. Create and activate a Python virtual environment:

   ```powershell
   py -3.13 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell prevents activation, use Command Prompt:

   ```bat
   .venv\Scripts\activate.bat
   ```

3. Install the project packages:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. Make a private local settings file:

   ```powershell
   Copy-Item .env.example .env
   ```

   Edit `.env` with your own values. Leave `DATABASE_URL` blank to use SQLite. Add AI and email credentials only if you want to use those features. Do not commit `.env` or paste its secrets into screenshots or chat.

5. Create/update the database tables and run Django’s configuration check:

   ```powershell
   python manage.py migrate
   python manage.py check
   ```

6. Start the local website:

   ```powershell
   python manage.py runserver
   ```

   Open <http://127.0.0.1:8000/> and register. The Django development server serves app CSS and JavaScript locally; if styles look stale after a change, hard-refresh the browser with **Ctrl+F5**.

To make an admin login for <http://127.0.0.1:8000/admin/>:

```powershell
python manage.py createsuperuser
```

### Local PDF note

WeasyPrint can require Windows native libraries in addition to Python packages. If PDF export reports a missing Pango or DLL library, follow the [WeasyPrint Windows installation instructions](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation).

## Environment settings

| Name | Required for | What to set |
| --- | --- | --- |
| `SECRET_KEY` | Django | A private random key. Use a different value for deployment. |
| `DEBUG` | Django | `True` for local work; `False` in production. |
| `ALLOWED_HOSTS` | Django | Comma-separated host names. Local default is `localhost,127.0.0.1`. |
| `DATABASE_URL` | Cloud database | Leave blank for local SQLite, or set a PostgreSQL connection URL. |
| `RESEND_API_KEY` | Email | Your Resend API key. Keep it private. |
| `DEFAULT_FROM_EMAIL` | Email | Sender allowed by Resend. `onboarding@resend.dev` is for Resend test delivery only; verify a domain in Resend to email real users. |
| `OPENAI_API_KEY` | Receipt AI and chat | Your API key for the configured OpenAI-compatible provider. |
| `OPENAI_BASE_URL` | Receipt AI and chat | API endpoint, default `https://api.deepseek.com`. |
| `OPENAI_RECEIPT_MODEL` | Receipt AI | Vision-capable model supported by your provider. Default `deepseek-flash`. |
| `OPENAI_CHAT_MODEL` | Finance chatbot | Chat model supported by your provider. Defaults to `OPENAI_RECEIPT_MODEL`. |
| `USE_CLOUD_STORAGE` | Cloud files | Set to `True` to store uploads in S3-compatible object storage. |
| `AWS_ENDPOINT_URL_S3` | Cloud files | S3-compatible service endpoint. |
| `AWS_ACCESS_KEY_ID` | Cloud files | Storage access key. |
| `AWS_SECRET_ACCESS_KEY` | Cloud files | Storage secret key. |
| `AWS_REGION` | Cloud files | Storage region. |
| `AWS_STORAGE_BUCKET_NAME` | Cloud files | Bucket name. |

## Email setup and test

BudgetAI uses Resend through Django’s email backend. In local `.env`, set `RESEND_API_KEY` and `DEFAULT_FROM_EMAIL`, then restart Django. Resend’s shared test sender can only deliver to permitted test recipients. To send to club members, add and verify a domain in Resend and use a sender address on that verified domain.

Send a diagnostic message with:

```powershell
python manage.py test_email delivered@resend.dev
```

Use a real recipient only after setting a verified sender. The command reports the selected Django backend and whether the provider accepted the message; it never prints the API key.

## Local database and cloud persistence

By default, local development uses `db.sqlite3`. That database is ignored by Git and stays on your own computer. Set `DATABASE_URL` to a PostgreSQL URL when you want to use a cloud database, then run:

```powershell
python manage.py migrate
```

The database and uploaded files are separate. To keep receipts and PDFs after a redeploy, configure a persistent S3-compatible bucket with all `AWS_*` settings and `USE_CLOUD_STORAGE=True`. When cloud storage is off, files are kept under local `media/` and will not automatically move to a cloud bucket. Existing local uploads need to be copied separately.

## Deployment notes

For a Railway deployment, configure environment variables in the Railway service settings; Railway does not read your local `.env`. Set `DATABASE_URL` to the attached PostgreSQL service, set `DEBUG=False`, provide the deployment host in `ALLOWED_HOSTS`, and add any email, AI, and storage values the deployed site needs.

Collect static assets as part of deployment so the finance stylesheet is available through WhiteNoise:

```sh
python manage.py collectstatic --noinput
```

Apply database migrations to the cloud database as part of deployment:

```sh
python manage.py migrate
```

A typical web process is:

```sh
gunicorn config.wsgi:application
```

After deploying, check the browser’s Network panel for `/static/finance/style.css` if a page looks unstyled, and check the service logs if email, AI, uploads, or PDF export fails. Never add `.env` or provider keys to Git.

## Project structure

```text
airost_project/
├── account/       # Custom user model, registration, sign-in, and account pages
├── clubs/         # Clubs, memberships, roles, and club pages
├── finance/       # Requests, review, transactions, receipts, reports, chat, email
├── config/        # Django settings, root routes, WSGI entry point
├── templates/     # Shared templates
├── static/        # Project-level static assets
├── manage.py      # Django command-line entry point
├── requirements.txt
├── .env.example   # Safe starter settings; copy to a private .env
└── .gitignore
```

Each Django app also has its own templates and static files.

## Before using with real club finances

- Set a strong private `SECRET_KEY`, `DEBUG=False`, and correct `ALLOWED_HOSTS` in deployment.
- Use managed PostgreSQL and persistent private object storage; check access controls for uploaded receipts.
- Verify Resend’s sending domain before emailing real club members.
- Check the active role/membership access in the deployed site using separate Member, Treasurer, and President accounts.
- Rotate credentials that were ever committed or shared. Removing a secret from the latest commit does not remove it from earlier Git history.

## License

No license has been added. Ask the project owner before reusing this project outside its intended academic use.
