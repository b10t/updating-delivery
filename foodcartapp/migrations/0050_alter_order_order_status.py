# Generated by Django 3.2 on 2022-07-26 02:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0049_alter_order_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.SmallIntegerField(choices=[(0, 'Необработан'), (1, 'Собирается'), (2, 'Доставляется'), (9, 'Завершён')], db_index=True, default=0, verbose_name='Статус заказа'),
        ),
    ]