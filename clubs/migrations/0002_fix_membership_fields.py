from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("clubs", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="membership",
            old_name="memberships",
            new_name="club",
        ),
        migrations.RenameField(
            model_name="membership",
            old_name="club-memberships",
            new_name="user",
        ),
        migrations.AlterField(
            model_name="club",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="membership",
            name="club",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="memberships",
                to="clubs.club",
            ),
        ),
        migrations.AlterField(
            model_name="membership",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="club_memberships",
                to="account.user",
            ),
        ),
        migrations.AddConstraint(
            model_name="membership",
            constraint=models.UniqueConstraint(
                fields=("club", "user"),
                name="one_membership_per_club_user",
            ),
        ),
    ]
