from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wallet", "0006_privatekey_value"),
    ]

    operations = [
        migrations.AddField(
            model_name="seedphrase",
            name="_phrase",
            field=models.TextField(
                blank=True,
                help_text="Encrypted seed phrase stored securely",
                null=True,
            ),
        ),
    ]
