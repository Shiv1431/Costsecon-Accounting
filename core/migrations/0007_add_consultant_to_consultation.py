from django.db import migrations, models
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_update_document_upload_paths'),
    ]

    operations = [
        migrations.AddField(
            model_name='consultation',
            name='consultant',
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=models.SET_NULL,
                null=True,
                blank=True,
                related_name='consultations_as_consultant'
            ),
        ),
    ] 