from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("topica", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="cluster",
            name="cohesion",
            field=models.FloatField(default=1.0),
            preserve_default=False,
        ),
    ]
