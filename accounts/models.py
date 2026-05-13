from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class Member(models.Model):
    name = models.CharField("姓名", max_length=40, unique=True)
    pin_hash = models.CharField("口令哈希", max_length=128)
    is_admin = models.BooleanField("管理员", default=False)
    is_active = models.BooleanField("启用", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "成员"
        verbose_name_plural = "成员"

    def __str__(self):
        return self.name

    def set_pin(self, raw_pin):
        self.pin_hash = make_password(raw_pin)

    def check_pin(self, raw_pin):
        return check_password(raw_pin, self.pin_hash)
