from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from accounts.models import Member


class StatusOption(models.Model):
    name = models.CharField("状态名称", max_length=40, unique=True)
    sort_order = models.PositiveIntegerField("排序", default=0)
    is_active = models.BooleanField("启用", default=True)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "工单状态"
        verbose_name_plural = "工单状态"

    def __str__(self):
        return self.name


class ImageTemplate(models.Model):
    name = models.CharField("模板名称", max_length=80)
    version = models.PositiveIntegerField("版本", default=1)
    is_active = models.BooleanField("当前启用", default=False)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    created_by = models.ForeignKey(
        Member,
        verbose_name="创建人",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_image_templates",
    )

    class Meta:
        ordering = ["-version", "-created_at"]
        verbose_name = "图片模板"
        verbose_name_plural = "图片模板"

    def __str__(self):
        return f"{self.name} v{self.version}"

    @classmethod
    def active(cls):
        return cls.objects.filter(is_active=True).prefetch_related("customer_items", "items").first()

    def publish(self):
        ImageTemplate.objects.exclude(pk=self.pk).update(is_active=False)
        self.is_active = True
        self.save(update_fields=["is_active"])

    def to_snapshot(self):
        return {
            "template_id": self.id,
            "name": self.name,
            "version": self.version,
            "customer_fields": [
                item.to_snapshot()
                for item in self.customer_items.filter(is_active=True).order_by("sort_order", "id")
            ],
            "items": [
                item.to_snapshot()
                for item in self.items.filter(is_active=True).order_by("sort_order", "id")
            ],
        }


class CustomerTemplateItem(models.Model):
    template = models.ForeignKey(
        ImageTemplate,
        verbose_name="模板",
        on_delete=models.CASCADE,
        related_name="customer_items",
    )
    key = models.SlugField("字段 key", max_length=80)
    label = models.CharField("字段名称", max_length=80)
    required = models.BooleanField("必填", default=False)
    help_text = models.CharField("说明", max_length=200, blank=True)
    sort_order = models.PositiveIntegerField("排序", default=0)
    is_active = models.BooleanField("启用", default=True)

    class Meta:
        ordering = ["sort_order", "id"]
        unique_together = [("template", "key")]
        verbose_name = "客户信息模板项"
        verbose_name_plural = "客户信息模板项"

    def __str__(self):
        return self.label

    def to_snapshot(self):
        return {
            "key": self.key,
            "label": self.label,
            "required": self.required,
            "help_text": self.help_text,
            "sort_order": self.sort_order,
        }


class ImageTemplateItem(models.Model):
    template = models.ForeignKey(
        ImageTemplate,
        verbose_name="模板",
        on_delete=models.CASCADE,
        related_name="items",
    )
    key = models.SlugField("字段 key", max_length=80)
    label = models.CharField("图片类别", max_length=80)
    required = models.BooleanField("必填", default=False)
    min_count = models.PositiveIntegerField("最少张数", default=0)
    help_text = models.CharField("说明", max_length=200, blank=True)
    sort_order = models.PositiveIntegerField("排序", default=0)
    is_active = models.BooleanField("启用", default=True)

    class Meta:
        ordering = ["sort_order", "id"]
        unique_together = [("template", "key")]
        verbose_name = "图片模板项"
        verbose_name_plural = "图片模板项"

    def __str__(self):
        return self.label

    def to_snapshot(self):
        return {
            "key": self.key,
            "label": self.label,
            "required": self.required,
            "min_count": self.min_count,
            "help_text": self.help_text,
            "sort_order": self.sort_order,
        }


class WorkOrder(models.Model):
    customer_name = models.CharField("客户姓名", max_length=80, blank=True, default="")
    customer_contact = models.CharField("联系方式", max_length=120, blank=True)
    customer_note = models.TextField("客户备注", blank=True)
    customer_data = models.JSONField("客户信息", default=dict, blank=True)
    status = models.ForeignKey(
        StatusOption,
        verbose_name="状态",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    creator = models.ForeignKey(
        Member,
        verbose_name="创建人",
        on_delete=models.PROTECT,
        related_name="created_orders",
    )
    template_snapshot = models.JSONField("图片模板快照", default=dict)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]
        verbose_name = "工单"
        verbose_name_plural = "工单"

    def __str__(self):
        return f"#{self.id} {self.customer_display}"

    def get_absolute_url(self):
        return reverse("order_detail", args=[self.pk])

    @property
    def template_items(self):
        return self.template_snapshot.get("items", [])

    @property
    def customer_fields(self):
        return self.template_snapshot.get("customer_fields", [])

    @property
    def customer_display(self):
        for field in self.customer_fields:
            value = self.customer_data.get(field["key"])
            if value:
                return value
        return self.customer_name or f"工单 {self.id}"

    @property
    def customer_preview_rows(self):
        rows = []
        for field in self.customer_fields[:2]:
            rows.append(
                {
                    "label": field.get("label", ""),
                    "value": self.customer_data.get(field["key"]) or "-",
                }
            )
        while len(rows) < 2:
            rows.append({"label": "", "value": "-"})
        return rows

    def image_warnings(self):
        warnings = []
        counts = {}
        for image in self.images.all():
            counts[image.template_key] = counts.get(image.template_key, 0) + 1

        snapshot_keys = {item["key"] for item in self.template_items}
        for item in self.template_items:
            count = counts.get(item["key"], 0)
            min_count = item.get("min_count", 0)
            if item.get("required") and count < min_count:
                warnings.append(f"{item['label']} 至少需要 {min_count} 张，当前 {count} 张。")

        for key, count in counts.items():
            if key and key not in snapshot_keys:
                warnings.append(f"存在 {count} 张无法匹配当前工单模板的历史图片：{key}。")
        return warnings


def order_image_upload_to(instance, filename):
    order_id = instance.order_id or "new"
    return f"orders/{order_id}/{instance.template_key}/{filename}"


class WorkOrderImage(models.Model):
    order = models.ForeignKey(
        WorkOrder,
        verbose_name="工单",
        on_delete=models.CASCADE,
        related_name="images",
    )
    template_key = models.CharField("模板字段 key", max_length=80)
    label = models.CharField("图片类别", max_length=80)
    image = models.ImageField("图片", upload_to=order_image_upload_to)
    note = models.CharField("说明", max_length=200, blank=True)
    uploaded_by = models.ForeignKey(
        Member,
        verbose_name="上传人",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_order_images",
    )
    created_at = models.DateTimeField("上传时间", auto_now_add=True)

    class Meta:
        ordering = ["template_key", "created_at"]
        verbose_name = "工单图片"
        verbose_name_plural = "工单图片"

    def __str__(self):
        return f"{self.order} - {self.label}"


def make_template_key(label, index):
    base = slugify(label) or f"field-{index}"
    return base[:70]
