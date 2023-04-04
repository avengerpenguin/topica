from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("topica", "0002_cluster_cohesion"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cluster",
            name="cohesion",
            field=models.FloatField(default=1.0),
        ),
    ]
