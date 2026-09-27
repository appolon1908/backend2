from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("lead_capture", "0003_leadsubmission_assignment_queue_and_more")]
    operations = [
        migrations.AddField(model_name="leadsubmission", name="content_locale", field=models.CharField(default="en", max_length=8)),
        migrations.AddField(model_name="leadsubmission", name="country_code", field=models.CharField(blank=True, max_length=2)),
        migrations.AddField(model_name="leadsubmission", name="locale_source", field=models.CharField(default="fallback", max_length=24)),
        migrations.AddField(model_name="leadsubmission", name="translation_version", field=models.CharField(blank=True, max_length=40)),
    ]
