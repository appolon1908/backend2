from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("payment_app", "0003_webhooksubscription_webhookdelivery")]
    operations = [
        migrations.AddField("webhooksubscription", "secret_ciphertext", models.TextField(default="")),
        migrations.AddField("webhooksubscription", "secret_nonce", models.CharField(default="", max_length=32)),
        migrations.AddField("webhooksubscription", "secret_key_version", models.CharField(default="v1", max_length=16)),
        migrations.AddField("webhooksubscription", "secret_fingerprint", models.CharField(db_index=True, default="", max_length=64)),
        migrations.AddField("webhooksubscription", "previous_secret_ciphertext", models.TextField(blank=True, default="")),
        migrations.AddField("webhooksubscription", "previous_secret_nonce", models.CharField(blank=True, default="", max_length=32)),
        migrations.AddField("webhooksubscription", "previous_secret_key_version", models.CharField(blank=True, default="", max_length=16)),
        migrations.AddField("webhooksubscription", "previous_secret_expires_at", models.DateTimeField(blank=True, null=True)),
        migrations.AddField("webhooksubscription", "secret_rotated_at", models.DateTimeField(blank=True, null=True)),
        migrations.AddField("webhooksubscription", "secret_revoked_at", models.DateTimeField(blank=True, null=True)),
    ]
