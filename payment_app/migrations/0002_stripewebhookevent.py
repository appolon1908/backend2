from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("payment_app", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="StripeWebhookEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_id", models.CharField(max_length=255, unique=True)),
                ("event_type", models.CharField(max_length=120)),
                ("payload_sha256", models.CharField(max_length=64)),
                ("status", models.CharField(default="received", max_length=24)),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("last_error", models.CharField(blank=True, max_length=255)),
                ("received_at", models.DateTimeField(auto_now_add=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.AddIndex(
            model_name="stripewebhookevent",
            index=models.Index(fields=["status", "received_at"], name="payment_app_status_6161a0_idx"),
        ),
    ]
