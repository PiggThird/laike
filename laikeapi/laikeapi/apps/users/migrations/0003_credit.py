# Generated by Django 3.2.9 on 2023-12-14 16:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_user_avatar'),
    ]

    operations = [
        migrations.CreateModel(
            name='Credit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=255, verbose_name='名称/标题')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='是否删除')),
                ('orders', models.IntegerField(default=0, verbose_name='序号')),
                ('is_show', models.BooleanField(default=True, verbose_name='是否显示')),
                ('created_time', models.DateTimeField(auto_now_add=True, verbose_name='添加时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('operation', models.SmallIntegerField(choices=[(0, '业务增值'), (1, '购物消费'), (2, '系统赠送')], default=1, verbose_name='积分操作类型')),
                ('number', models.IntegerField(default=0, help_text='如果是扣除积分则需要设置积分为负数，如果消费10积分，则填写-10，<br>如果是添加积分则需要设置积分为正数，如果获得10积分，则填写10。', verbose_name='积分数量')),
                ('remark', models.CharField(blank=True, max_length=500, null=True, verbose_name='备注信息')),
                ('user', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, related_name='user_credits', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '积分流水',
                'verbose_name_plural': '积分流水',
                'db_table': 'lk_credit',
            },
        ),
    ]
