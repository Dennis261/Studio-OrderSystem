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


class ActivityLog(models.Model):
    class Action(models.TextChoices):
        LOGIN = "login", "登录"
        LOGOUT = "logout", "退出"
        MEMBER_SAVE = "member_save", "保存成员"
        ORDER_CREATE = "order_create", "创建工单"
        ORDER_TAGS_UPDATE = "order_tags_update", "更新工单标签"
        ORDER_ARCHIVE_UPDATE = "order_archive_update", "更新归档状态"
        POST_CREATE = "post_create", "发布跟帖"
        STATUS_SAVE = "status_save", "保存状态标签"
        TEMPLATE_PUBLISH = "template_publish", "发布模板"
        TODO_READ = "todo_read", "阅读待办"
        TODO_DONE = "todo_done", "完成待办"

    actor = models.ForeignKey(
        Member,
        verbose_name="操作人",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="activity_logs",
    )
    action = models.CharField("操作类型", max_length=40, choices=Action.choices)
    target_type = models.CharField("对象类型", max_length=80, blank=True)
    target_id = models.PositiveBigIntegerField("对象 ID", null=True, blank=True)
    target_repr = models.CharField("对象名称", max_length=160, blank=True)
    summary = models.TextField("摘要", blank=True)
    metadata = models.JSONField("详情", default=dict, blank=True)
    ip_address = models.GenericIPAddressField("IP 地址", null=True, blank=True)
    user_agent = models.CharField("浏览器", max_length=255, blank=True)
    created_at = models.DateTimeField("操作时间", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "操作日志"
        verbose_name_plural = "操作日志"

    def __str__(self):
        actor = self.actor.name if self.actor else "系统"
        return f"{actor} {self.get_action_display()}"
