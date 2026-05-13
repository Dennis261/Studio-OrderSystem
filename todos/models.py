from django.db import models

from accounts.models import Member
from orders.models import WorkOrder
from threads.models import Post


class Todo(models.Model):
    class Status(models.TextChoices):
        UNREAD = "unread", "未读"
        READ = "read", "已读"
        DONE = "done", "已完成"

    order = models.ForeignKey(
        WorkOrder,
        verbose_name="工单",
        on_delete=models.CASCADE,
        related_name="todos",
    )
    source_post = models.ForeignKey(
        Post,
        verbose_name="来源跟帖",
        on_delete=models.CASCADE,
        related_name="todos",
    )
    target = models.ForeignKey(
        Member,
        verbose_name="处理人",
        on_delete=models.CASCADE,
        related_name="todos",
    )
    status = models.CharField(
        "状态",
        max_length=20,
        choices=Status.choices,
        default=Status.UNREAD,
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    read_at = models.DateTimeField("阅读时间", null=True, blank=True)
    done_at = models.DateTimeField("完成时间", null=True, blank=True)

    class Meta:
        ordering = ["status", "-created_at"]
        unique_together = [("source_post", "target")]
        verbose_name = "待办"
        verbose_name_plural = "待办"

    def __str__(self):
        return f"{self.target} - {self.order}"
