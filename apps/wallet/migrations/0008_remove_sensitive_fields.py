from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("wallet", "0007_seedphrase_phrase"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="seedphrase",
            name="_phrase",
        ),
        migrations.RemoveField(
            model_name="privatekey",
            name="_private_key_value",
        ),
    ]
