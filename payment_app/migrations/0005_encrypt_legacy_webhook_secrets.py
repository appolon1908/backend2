from django.db import migrations


def encrypt_legacy(apps, schema_editor):
    Model = apps.get_model("payment_app", "WebhookSubscription")
    from payment_app.secret_crypto import encrypt, fingerprint
    for row in Model.objects.exclude(secret="").iterator():
        ciphertext, nonce = encrypt(row.secret)
        row.secret_ciphertext = ciphertext
        row.secret_nonce = nonce
        row.secret_fingerprint = fingerprint(row.secret)
        row.save(update_fields=["secret_ciphertext", "secret_nonce", "secret_fingerprint"])


class Migration(migrations.Migration):
    dependencies = [("payment_app", "0004_webhook_secret_envelope")]
    operations = [migrations.RunPython(encrypt_legacy, migrations.RunPython.noop), migrations.RemoveField("webhooksubscription", "secret")]
