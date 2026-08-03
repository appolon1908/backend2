import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("payment_app", "0005_encrypt_legacy_webhook_secrets")]
    operations = [migrations.CreateModel(
        name="WebhookAuditEvent",
        fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("action", models.CharField(max_length=32)),
            ("metadata", models.JSONField(default=dict)),
            ("occurred_at", models.DateTimeField(auto_now_add=True)),
            ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ("subscription", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="payment_app.webhooksubscription")),
        ],
    )]
