from django.conf import settings
from django.core.mail import get_connection, send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Send one test email using the configured SMTP settings."

    def add_arguments(self, parser):
        parser.add_argument("recipient", help="Email address to receive the test message")

    def handle(self, *args, **options):
        recipient = options["recipient"]

        if settings.EMAIL_BACKEND != "django.core.mail.backends.smtp.EmailBackend":
            raise CommandError(
                "Django is using the console email backend, not SMTP. "
                "Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in this environment first."
            )

        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            raise CommandError(
                "SMTP credentials are missing. Set EMAIL_HOST_USER and "
                "EMAIL_HOST_PASSWORD in this environment."
            )

        if settings.EMAIL_USE_TLS and settings.EMAIL_USE_SSL:
            raise CommandError(
                "EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be enabled."
            )

        self.stdout.write("BudgetAI SMTP test configuration:")
        self.stdout.write(f"  Host: {settings.EMAIL_HOST}")
        self.stdout.write(f"  Port: {settings.EMAIL_PORT}")
        self.stdout.write(f"  TLS: {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"  SSL: {settings.EMAIL_USE_SSL}")
        self.stdout.write(f"  From: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"  To: {recipient}")
        self.stdout.write("  SMTP password: hidden")
        self.stdout.write("Connecting and sending (10 second connection timeout)...")

        # Use an explicit timeout so this diagnostic command cannot hang indefinitely.
        connection = get_connection(fail_silently=False, timeout=10)
        try:
            sent_count = send_mail(
                subject="BudgetAI SMTP test",
                message=(
                    "This is a test message from BudgetAI. "
                    "Your configured Django email connection can send email."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
                connection=connection,
            )
        except Exception as exc:
            raise CommandError(
                f"SMTP test failed ({type(exc).__name__}): {exc}"
            ) from exc

        if sent_count != 1:
            raise CommandError(
                f"SMTP backend reported {sent_count} messages sent; expected 1."
            )

        self.stdout.write(self.style.SUCCESS("Test email sent successfully."))
