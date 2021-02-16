from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("topica", "0003_auto_20150918_1835"),
    ]

    operations = [
        migrations.CreateModel(
            name="ClusterLinkage",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("value", models.FloatField()),
                (
                    "from_cluster",
                    models.ForeignKey(
                        related_name="from_clusters", to="topica.Cluster"
                    ),
                ),
                (
                    "to_cluster",
                    models.ForeignKey(
                        related_name="to_clusters", to="topica.Cluster"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="cluster",
            name="linkages",
            field=models.ManyToManyField(
                to="topica.Cluster", through="topica.ClusterLinkage"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="clusterlinkage",
            unique_together={("from_cluster", "to_cluster")},
        ),
    ]
