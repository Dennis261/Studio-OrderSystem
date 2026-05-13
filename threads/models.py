from django.db import models

from accounts.models import Member
from orders.models import WorkOrder


class Post(models.Model):
    order = models.ForeignKey(
        WorkOrder,
        verbose_name="工单",
        on_delete=models.CASCADE,
        related_name="posts",
    )
    author = models.ForeignKey(
        Member,
        verbose_name="发布人",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="posts",
    )
    body = models.TextField("内容")
    created_at = models.DateTimeField("发布时间", auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "跟帖"
        verbose_name_plural = "跟帖"

    def __str__(self):
        return f"{self.order} - {self.author}"


def post_attachment_upload_to(instance, filename):
    return f"orders/{instance.post.order_id}/posts/{instance.post_id}/{filename}"


class PostAttachment(models.Model):
    post = models.ForeignKey(
        Post,
        verbose_name="跟帖",
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    image = models.ImageField("图片", upload_to=post_attachment_upload_to)
    uploaded_at = models.DateTimeField("上传时间", auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]
        verbose_name = "跟帖附件"
        verbose_name_plural = "跟帖附件"

    def __str__(self):
        return self.image.name
