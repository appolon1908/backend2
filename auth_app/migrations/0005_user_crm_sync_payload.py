from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("auth_app", "0004_user_crm_sync_state")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="crm_sync_payload",
            field=models.JSONField(default=dict, blank=True),
        ),
    ]
