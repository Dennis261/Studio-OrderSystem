from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("threads", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="postattachment",
            old_name="file",
            new_name="image",
        ),
    ]
