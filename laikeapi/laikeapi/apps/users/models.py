from django.db import models
from django.contrib.auth.models import AbstractUser
from stdimage import StdImageField
from django.utils.safestring import mark_safe

# Create your models here.


class User(AbstractUser):
    mobile = models.CharField(max_length=15, unique=True, verbose_name='手机号')
    money = models.DecimalField(max_digits=9, default=0.0, decimal_places=2, verbose_name="钱包余额")
    credit = models.IntegerField(default=0, verbose_name="积分")
    # avatar = models.ImageField(upload_to="avatar/%Y", null=True, default="", verbose_name="个人头像")
    avatar = StdImageField(variations={
        'thumb_400x400': (400, 400),  # 'medium': (400, 400),
        'thumb_50x50': (50, 50, True),  # 'small': (50, 50, True),
    }, delete_orphans=True, upload_to="avatar/%Y", blank=True, null=True, verbose_name="个人头像")
    nickname = models.CharField(max_length=50, default="", null=True, verbose_name="用户昵称")

    class Meta:
        db_table = 'lk_users'
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name

    def avatar_small(self):
        if self.avatar:
            return mark_safe(f'<img style="border-radius: 100%;" src="{self.avatar.thumb_50x50.url}">')
        return ""

    avatar_small.short_description = "个人头像(50x50)"
    avatar_small.allow_tags = True
    avatar_small.admin_order_field = "avatar"

    def avatar_medium(self):
        if self.avatar:
            return mark_safe(f'<img style="border-radius: 100%;" src="{self.avatar.thumb_400x400.url}">')
        return ""

    avatar_medium.short_description = "个人头像(400x400)"
    avatar_medium.allow_tags = True
    avatar_medium.admin_order_field = "avatar"