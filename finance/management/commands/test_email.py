from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Send one test email through the email provider configured in Django."

    def add_arguments(self, parser):
        parser.add_argument("recipient", help="Address to receive the test email")

    def handle(self, *args, **options):
        recipient = options["recipient"]
        if not settings.DEFAULT_FROM_EMAIL:
            raise CommandError("DEFAULT_FROM_EMAIL is not configured.")

        self.stdout.write(f"Email backend: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"From: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"To: {recipient}")
        try:
            sent_count = send_mail(
                subject="BudgetAI email delivery test",
                message=("This is a test message from BudgetAI. "
                         "The configured email provider accepted this message."),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
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
