from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("auth_app", "0003_alter_visitor_page")]
    operations = [
        migrations.AddField(model_name="user", name="crm_sync_status", field=models.CharField(default="pending", max_length=20)),
        migrations.AddField(model_name="user", name="crm_sync_operation_id", field=models.CharField(blank=True, default="", max_length=128)),
        migrations.AddField(model_name="user", name="crm_sync_last_error", field=models.CharField(blank=True, default="", max_length=1000)),
        migrations.AddField(model_name="user", name="crm_synced_at", field=models.DateTimeField(blank=True, null=True)),
    ]
