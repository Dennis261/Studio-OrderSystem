from django import forms
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.activity import log_activity
from accounts.decorators import admin_member_required, member_required
from accounts.models import ActivityLog, Member
from threads.forms import PostForm
from threads.models import PostAttachment
from threads.services import create_todos_for_mentions
from todos.models import Todo

from .forms import ImageTemplateForm, StatusOptionForm, WorkOrderForm
from .models import ImageTemplate, StatusOption, WorkOrder, WorkOrderImage


@member_required
def dashboard(request):
    orders = (
        WorkOrder.objects.prefetch_related("tags")
        .filter(is_archived=False)
        .order_by("-updated_at")[:10]
    )
    my_todos = (
        Todo.objects.filter(target=request.current_member)
        .exclude(status=Todo.Status.DONE)
        .select_related("order", "source_post", "source_post__author")[:8]
    )
    return render(
        request,
        "orders/dashboard.html",
        {
            "orders": orders,
            "my_todos": my_todos,
            "statuses": StatusOption.objects.filter(is_active=True),
        },
    )


@member_required
def order_list(request):
    status_id = request.GET.get("status")
    show_archived = request.GET.get("archived") == "1"
    mine = request.GET.get("mine") == "1"
    orders = WorkOrder.objects.prefetch_related("tags")
    if not show_archived:
        orders = orders.filter(is_archived=False)
    if status_id:
        orders = orders.filter(tags__id=status_id)
    if mine:
        orders = orders.filter(todos__target=request.current_member).exclude(
            todos__status=Todo.Status.DONE
        )
    return render(
        request,
        "orders/list.html",
        {
            "orders": orders.distinct(),
            "statuses": StatusOption.objects.filter(is_active=True),
            "status_id": status_id,
            "show_archived": show_archived,
            "mine": mine,
        },
    )


@admin_member_required
@transaction.atomic
def order_create(request):
    template = ImageTemplate.active()
    if template is None:
        messages.error(request, "请先由管理员创建并发布图片模板。")
        return redirect("dashboard")

    template_snapshot = template.to_snapshot()
    form = WorkOrderForm(request.POST or None, template_snapshot=template_snapshot)
    if request.method == "GET":
        default_tag = StatusOption.objects.filter(name="新建", is_active=True).first()
        if default_tag:
            form.fields["tags"].initial = [default_tag]

    if request.method == "POST" and form.is_valid():
        customer_data = form.customer_data()
        order = WorkOrder.objects.create(
            customer_name=_first_customer_value(template_snapshot, customer_data),
            customer_data=customer_data,
            template_snapshot=template_snapshot,
        )
        selected_tags = form.cleaned_data.get("tags")
        if selected_tags:
            order.tags.set(selected_tags)
        else:
            default_tag = StatusOption.objects.filter(name="新建", is_active=True).first()
            if default_tag:
                order.tags.add(default_tag)
        _save_order_images(order, request, request.current_member)
        log_activity(
            request,
            ActivityLog.Action.ORDER_CREATE,
            target=order,
            summary=f"创建工单：{order.customer_display}",
            metadata={
                "tags": list(order.tags.values_list("name", flat=True)),
                "template": template_snapshot.get("name", ""),
                "template_version": template_snapshot.get("version"),
            },
        )
        messages.success(request, "工单已创建。")
        return redirect(order)

    return render(
        request,
        "orders/new.html",
        {
            "form": form,
            "template": template,
            "customer_fields": template_snapshot["customer_fields"],
            "template_items": template_snapshot["items"],
        },
    )


@member_required
@transaction.atomic
def order_detail(request, pk):
    order = get_object_or_404(
        WorkOrder.objects.prefetch_related(
            "tags", "images", "posts__author", "posts__attachments", "posts__todos"
        ),
        pk=pk,
    )

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update_tags":
            before_tags = list(order.tags.values_list("name", flat=True))
            tags = StatusOption.objects.filter(pk__in=request.POST.getlist("tags"), is_active=True)
            order.tags.set(tags)
            order.save(update_fields=["updated_at"])
            after_tags = list(order.tags.values_list("name", flat=True))
            log_activity(
                request,
                ActivityLog.Action.ORDER_TAGS_UPDATE,
                target=order,
                summary=f"更新工单标签：{order.customer_display}",
                metadata={"before": before_tags, "after": after_tags},
            )
            messages.success(request, "状态标签已更新。")
            return redirect(order)

        if action == "update_archive":
            before_archived = order.is_archived
            order.is_archived = request.POST.get("is_archived") == "1"
            order.save(update_fields=["is_archived", "updated_at"])
            log_activity(
                request,
                ActivityLog.Action.ORDER_ARCHIVE_UPDATE,
                target=order,
                summary=f"{'归档' if order.is_archived else '取消归档'}工单：{order.customer_display}",
                metadata={"before": before_archived, "after": order.is_archived},
            )
            messages.success(request, "归档状态已更新。")
            return redirect(order)

        if action == "add_post":
            post_form = PostForm(request.POST)
            if post_form.is_valid():
                attachments = request.FILES.getlist("attachments")
                invalid_images = _invalid_post_images(attachments)
                if invalid_images:
                    messages.error(request, f"跟帖只支持上传图片：{', '.join(invalid_images)}")
                else:
                    post = post_form.save(commit=False)
                    post.order = order
                    post.author = request.current_member
                    post.save()
                    for image in attachments:
                        PostAttachment.objects.create(post=post, image=image)
                    todos = create_todos_for_mentions(post)
                    order.save(update_fields=["updated_at"])
                    log_activity(
                        request,
                        ActivityLog.Action.POST_CREATE,
                        target=order,
                        summary=f"发布跟帖：{order.customer_display}",
                        metadata={
                            "post_id": post.id,
                            "attachments": len(attachments),
                            "todos": len(todos),
                        },
                    )
                    messages.success(request, f"跟帖已发布，生成 {len(todos)} 条待办。")
                    return redirect(f"{order.get_absolute_url()}#post-{post.id}")
        else:
            post_form = PostForm()
    else:
        post_form = PostForm()

    images_by_key = {}
    for image in order.images.all():
        images_by_key.setdefault(image.template_key, []).append(image)
    template_sections = [
        {"item": item, "images": images_by_key.get(item["key"], [])}
        for item in order.template_items
    ]

    return render(
        request,
        "orders/detail.html",
        {
            "order": order,
            "post_form": post_form,
            "statuses": StatusOption.objects.filter(is_active=True),
            "members": Member.objects.filter(is_active=True),
            "customer_rows": _customer_rows(order),
            "template_sections": template_sections,
            "warnings": order.image_warnings(),
            "active_tag_ids": list(order.tags.values_list("id", flat=True)),
            "my_open_todos": order.todos.filter(target=request.current_member).exclude(
                status=Todo.Status.DONE
            ),
        },
    )


@admin_member_required
def manage_statuses(request):
    form = StatusOptionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        status = form.save()
        log_activity(
            request,
            ActivityLog.Action.STATUS_SAVE,
            target=status,
            summary=f"保存状态标签：{status.name}",
            metadata={"sort_order": status.sort_order, "is_active": status.is_active},
        )
        messages.success(request, "状态已保存。")
        return redirect("manage_statuses")
    return render(
        request,
        "manage/statuses.html",
        {
            "form": form,
            "statuses": StatusOption.objects.all(),
        },
    )


@admin_member_required
def manage_templates(request):
    current = ImageTemplate.active()
    initial = {"name": current.name} if current else {"name": "默认模板"}
    form = ImageTemplateForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        template = form.save(request.current_member)
        log_activity(
            request,
            ActivityLog.Action.TEMPLATE_PUBLISH,
            target=template,
            summary=f"发布模板：{template.name} v{template.version}",
            metadata={
                "customer_fields": template.customer_items.count(),
                "image_items": template.items.count(),
            },
        )
        messages.success(request, "新模板版本已发布，只会影响之后创建的工单。")
        return redirect("manage_templates")

    customer_rows, image_rows = _template_editor_rows(request, current)
    return render(
        request,
        "manage/templates.html",
        {
            "form": form,
            "current": current,
            "customer_rows": customer_rows,
            "image_rows": image_rows,
            "templates": ImageTemplate.objects.prefetch_related("customer_items", "items")[:10],
        },
    )


def _save_order_images(order, request, member):
    item_by_key = {item["key"]: item for item in order.template_items}
    for key, item in item_by_key.items():
        for image in request.FILES.getlist(f"image_{key}"):
            WorkOrderImage.objects.create(
                order=order,
                template_key=key,
                label=item["label"],
                image=image,
                uploaded_by=member,
            )


def _invalid_post_images(files):
    image_field = forms.ImageField()
    invalid = []
    for file_obj in files:
        try:
            image_field.clean(file_obj)
        except forms.ValidationError:
            invalid.append(file_obj.name)
        finally:
            try:
                file_obj.seek(0)
            except (AttributeError, OSError):
                pass
    return invalid


def _first_customer_value(template_snapshot, customer_data):
    for field in template_snapshot.get("customer_fields", []):
        value = customer_data.get(field["key"])
        if value:
            return value
    return ""


def _customer_rows(order):
    return [
        {
            "label": field["label"],
            "value": order.customer_data.get(field["key"], ""),
            "required": field.get("required", False),
            "help_text": field.get("help_text", ""),
        }
        for field in order.customer_fields
    ]


def _template_editor_rows(request, current):
    if request.method == "POST":
        return _rows_from_post(request, "customer"), _rows_from_post(request, "image")
    if current:
        return (
            [
                {
                    "index": index,
                    "label": item.label,
                    "required": item.required,
                    "help_text": item.help_text,
                }
                for index, item in enumerate(current.customer_items.filter(is_active=True), start=1)
            ],
            [
                {
                    "index": index,
                    "label": item.label,
                    "required": item.required,
                    "min_count": item.min_count,
                    "help_text": item.help_text,
                }
                for index, item in enumerate(current.items.filter(is_active=True), start=1)
            ],
        )
    return (
        [
            {"index": 1, "label": "客户姓名", "required": True, "help_text": ""},
            {"index": 2, "label": "联系方式", "required": False, "help_text": ""},
            {"index": 3, "label": "客户备注", "required": False, "help_text": ""},
        ],
        [
            {"index": 1, "label": "客户原图", "required": True, "min_count": 1, "help_text": "客户提供的原始图片。"},
            {"index": 2, "label": "细节图", "required": False, "min_count": 0, "help_text": ""},
            {"index": 3, "label": "参考图", "required": False, "min_count": 0, "help_text": ""},
        ],
    )


def _rows_from_post(request, prefix):
    rows = []
    for index in request.POST.getlist(f"{prefix}_indices"):
        label = request.POST.get(f"{prefix}_label_{index}", "").strip()
        if not label:
            continue
        row = {
            "index": index,
            "label": label,
            "required": request.POST.get(f"{prefix}_required_{index}") == "on",
            "help_text": request.POST.get(f"{prefix}_help_{index}", "").strip(),
        }
        if prefix == "image":
            row["min_count"] = request.POST.get(f"{prefix}_min_count_{index}", "0")
        rows.append(row)
    return rows
