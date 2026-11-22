from django.conf import settings
from django.core.mail import get_connection, send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Send one test email through the configured SMTP server."

    def add_arguments(self, parser):
        parser.add_argument("recipient", help="Address to receive the test email")

    def handle(self, *args, **options):
        recipient = options["recipient"]
        if settings.EMAIL_BACKEND != "django.core.mail.backends.smtp.EmailBackend":
            raise CommandError(
                "The configured email backend is not Django SMTP. Set EMAIL_BACKEND "
                "to django.core.mail.backends.smtp.EmailBackend."
            )

        missing = [
            name for name, value in {
                "EMAIL_HOST": settings.EMAIL_HOST,
                "EMAIL_HOST_USER": settings.EMAIL_HOST_USER,
                "EMAIL_HOST_PASSWORD": settings.EMAIL_HOST_PASSWORD,
                "DEFAULT_FROM_EMAIL": settings.DEFAULT_FROM_EMAIL,
            }.items() if not value
        ]
        if missing:
            raise CommandError("Missing SMTP settings: " + ", ".join(missing))

        if settings.EMAIL_USE_TLS and settings.EMAIL_USE_SSL:
            raise CommandError("EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be enabled.")

        self.stdout.write("BudgetAI SMTP test configuration:")
        self.stdout.write(f"Host: {settings.EMAIL_HOST}")
        self.stdout.write(f"Port: {settings.EMAIL_PORT}")
        self.stdout.write(f"TLS: {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"SSL: {settings.EMAIL_USE_SSL}")
        self.stdout.write(f"From: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"To: {recipient}")
        self.stdout.write("SMTP password: hidden")
        try:
            connection = get_connection(fail_silently=False)
            sent_count = send_mail(
                subject="BudgetAI email delivery test",
                message=("This is a test message from BudgetAI. "
                         "The configured email provider accepted this message."),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
                connection=connection,
            )
        except Exception as exc:
            raise CommandError(
                f"Email test failed ({type(exc).__name__}): {exc}"
            ) from exc

        if sent_count != 1:
            raise CommandError(
                f"Email backend reported {sent_count} messages sent; expected 1."
            )
        self.stdout.write(self.style.SUCCESS("Test email sent successfully."))
