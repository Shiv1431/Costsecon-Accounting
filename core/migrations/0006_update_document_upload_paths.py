from django.db import migrations, models
from core.models import document_upload_path

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_add_meeting_link_sent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='file',
            field=models.FileField(upload_to=document_upload_path),
        ),
        migrations.AlterField(
            model_name='consultation',
            name='supporting_documents',
            field=models.FileField(blank=True, null=True, upload_to=document_upload_path),
        ),
        migrations.AlterField(
            model_name='consultation',
            name='additional_documents',
            field=models.FileField(blank=True, null=True, upload_to=document_upload_path),
        ),
    ] 