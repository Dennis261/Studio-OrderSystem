import threads.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("threads", "0002_rename_postattachment_file_to_image"),
    ]

    operations = [
        migrations.AlterField(
            model_name="postattachment",
            name="image",
            field=models.ImageField(upload_to=threads.models.post_attachment_upload_to, verbose_name="图片"),
        ),
    ]
