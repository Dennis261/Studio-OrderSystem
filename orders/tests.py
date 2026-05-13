from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from accounts.models import Member
from threads.models import Post, PostAttachment
from threads.services import create_todos_for_mentions
from todos.models import Todo

from .models import CustomerTemplateItem, ImageTemplate, ImageTemplateItem, StatusOption, WorkOrder


class WorkOrderModelTests(TestCase):
    def setUp(self):
        self.member = Member.objects.create(name="客服小王")
        self.member.set_pin("123456")
        self.member.save()
        self.status = StatusOption.objects.create(name="新建")
        self.template = ImageTemplate.objects.create(name="默认模板", version=1, is_active=True)
        CustomerTemplateItem.objects.create(
            template=self.template,
            key="customer-name",
            label="客户姓名",
            required=True,
        )
        ImageTemplateItem.objects.create(
            template=self.template,
            key="original",
            label="客户原图",
            required=True,
            min_count=1,
        )

    def test_order_locks_template_snapshot(self):
        order = WorkOrder.objects.create(
            customer_name="张三",
            status=self.status,
            creator=self.member,
            template_snapshot=self.template.to_snapshot(),
        )
        self.template.is_active = False
        self.template.save()
        new_template = ImageTemplate.objects.create(name="新模板", version=2, is_active=True)
        ImageTemplateItem.objects.create(
            template=new_template,
            key="new-detail",
            label="新细节",
            required=True,
            min_count=2,
        )

        order.refresh_from_db()
        self.assertEqual(order.template_snapshot["version"], 1)
        self.assertEqual(order.template_snapshot["customer_fields"][0]["key"], "customer-name")
        self.assertEqual(order.template_snapshot["items"][0]["key"], "original")

    def test_missing_required_image_warns_without_blocking(self):
        order = WorkOrder.objects.create(
            customer_name="张三",
            status=self.status,
            creator=self.member,
            template_snapshot=self.template.to_snapshot(),
        )

        self.assertEqual(order.image_warnings(), ["客户原图 至少需要 1 张，当前 0 张。"])


class MentionTodoTests(TestCase):
    def setUp(self):
        self.author = Member.objects.create(name="客服小王")
        self.author.set_pin("123456")
        self.author.save()
        self.target = Member.objects.create(name="建模小李")
        self.target.set_pin("123456")
        self.target.save()
        self.status = StatusOption.objects.create(name="新建")
        self.order = WorkOrder.objects.create(
            customer_name="张三",
            status=self.status,
            creator=self.author,
            customer_data={"customer-name": "张三"},
            template_snapshot={"customer_fields": [{"key": "customer-name", "label": "客户姓名"}], "items": []},
        )

    def test_duplicate_mentions_create_one_todo(self):
        post = Post.objects.create(
            order=self.order,
            author=self.author,
            body="@建模小李 请处理，@建模小李 辛苦。",
        )
        todos = create_todos_for_mentions(post)

        self.assertEqual(len(todos), 1)
        self.assertEqual(Todo.objects.count(), 1)
        self.assertEqual(Todo.objects.get().target, self.target)


class ViewTests(TestCase):
    def setUp(self):
        self.admin = Member.objects.create(name="管理员", is_admin=True)
        self.admin.set_pin("123456")
        self.admin.save()
        self.member = Member.objects.create(name="普通成员")
        self.member.set_pin("123456")
        self.member.save()
        self.status = StatusOption.objects.create(name="新建")
        self.template = ImageTemplate.objects.create(name="默认模板", version=1, is_active=True)
        CustomerTemplateItem.objects.create(
            template=self.template,
            key="customer-name",
            label="客户姓名",
            required=True,
        )
        self.order = WorkOrder.objects.create(
            customer_name="张三",
            status=self.status,
            creator=self.member,
            customer_data={"customer-name": "张三"},
            template_snapshot=self.template.to_snapshot(),
        )
        self.post = Post.objects.create(order=self.order, author=self.admin, body="@普通成员 处理")
        self.todo = Todo.objects.create(order=self.order, source_post=self.post, target=self.member)

    def login_as(self, member):
        session = self.client.session
        session["member_id"] = member.id
        session.save()

    def test_business_page_requires_login(self):
        response = self.client.get(reverse("order_list"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))

    def test_member_can_login_with_pin(self):
        response = self.client.post(
            reverse("login"),
            {"member": self.member.id, "pin": "123456"},
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(self.client.session["member_id"], self.member.id)

    def test_non_admin_cannot_access_manage_page(self):
        self.login_as(self.member)
        response = self.client.get(reverse("manage_members"))
        self.assertRedirects(response, reverse("dashboard"))

    def test_non_admin_cannot_create_order(self):
        self.login_as(self.member)
        response = self.client.get(reverse("order_create"))
        self.assertRedirects(response, reverse("dashboard"))

    def test_admin_can_create_order_with_template_customer_data(self):
        self.login_as(self.admin)
        response = self.client.post(
            reverse("order_create"),
            {
                "status": self.status.id,
                "customer_customer-name": "李四",
            },
        )
        self.assertEqual(response.status_code, 302)
        order = WorkOrder.objects.exclude(pk=self.order.pk).get()
        self.assertEqual(order.customer_data["customer-name"], "李四")
        self.assertEqual(order.customer_display, "李四")

    def test_open_todo_marks_read(self):
        self.login_as(self.member)
        response = self.client.get(reverse("todo_open", args=[self.todo.id]))
        self.assertEqual(response.status_code, 302)
        self.todo.refresh_from_db()
        self.assertEqual(self.todo.status, Todo.Status.READ)

    def test_complete_todo_marks_done(self):
        self.login_as(self.member)
        response = self.client.post(reverse("todo_done", args=[self.todo.id]))
        self.assertEqual(response.status_code, 302)
        self.todo.refresh_from_db()
        self.assertEqual(self.todo.status, Todo.Status.DONE)

    def test_order_list_filters_by_my_open_todos(self):
        self.login_as(self.member)
        response = self.client.get(reverse("order_list"), {"mine": "1"})
        self.assertContains(response, "张三")

    def test_dashboard_uses_compact_order_table(self):
        self.login_as(self.member)
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "信息 1")
        self.assertNotContains(response, "<th>状态</th>", html=True)
        self.assertNotContains(response, "<th>创建人</th>", html=True)
        self.assertNotContains(response, "<th>更新时间</th>", html=True)

    def test_post_rejects_non_image_attachment(self):
        self.login_as(self.member)
        upload = SimpleUploadedFile("note.txt", b"not an image", content_type="text/plain")
        response = self.client.post(
            reverse("order_detail", args=[self.order.id]),
            {"action": "add_post", "body": "补充一张图", "attachments": upload},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "跟帖只支持上传图片")
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(PostAttachment.objects.count(), 0)

    def test_post_image_attachment_renders_preview(self):
        self.login_as(self.member)
        upload = SimpleUploadedFile("preview.png", _tiny_png(), content_type="image/png")
        response = self.client.post(
            reverse("order_detail", args=[self.order.id]),
            {"action": "add_post", "body": "图片预览", "attachments": upload},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PostAttachment.objects.count(), 1)
        self.assertContains(response, 'class="attachment-preview"')
        self.assertContains(response, "<img")


def _tiny_png():
    output = BytesIO()
    Image.new("RGB", (1, 1), color=(13, 107, 95)).save(output, format="PNG")
    return output.getvalue()
