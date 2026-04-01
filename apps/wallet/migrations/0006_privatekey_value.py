from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wallet", "0005_privatekey"),
    ]

    operations = [
        migrations.AddField(
            model_name="privatekey",
            name="_private_key_value",
            field=models.TextField(
                blank=True,
                help_text="Encrypted private key stored securely",
                null=True,
            ),
        ),
    ]
