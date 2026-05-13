from django.core.management.base import BaseCommand

from accounts.models import Member
from orders.models import CustomerTemplateItem, ImageTemplate, ImageTemplateItem, StatusOption


class Command(BaseCommand):
    help = "Create default members, statuses, and templates for local use."

    def handle(self, *args, **options):
        members = [
            ("管理员", True, "123456"),
            ("客服小王", False, "123456"),
            ("建模小李", False, "123456"),
            ("生产小张", False, "123456"),
        ]
        for name, is_admin, pin in members:
            member, created = Member.objects.get_or_create(
                name=name,
                defaults={"is_admin": is_admin, "is_active": True},
            )
            member.is_admin = is_admin
            if created or not member.pin_hash:
                member.set_pin(pin)
            member.save()

        for index, name in enumerate(
            ["新建", "建模中", "待确认", "待生产", "生产中", "已发货", "已完成"],
            start=1,
        ):
            StatusOption.objects.get_or_create(name=name, defaults={"sort_order": index})

        if not ImageTemplate.objects.exists():
            admin = Member.objects.filter(is_admin=True).first()
            template = ImageTemplate.objects.create(
                name="默认工单模板",
                version=1,
                is_active=True,
                created_by=admin,
            )
            CustomerTemplateItem.objects.bulk_create(
                [
                    CustomerTemplateItem(
                        template=template,
                        key="customer-name",
                        label="客户姓名",
                        required=True,
                        sort_order=1,
                    ),
                    CustomerTemplateItem(
                        template=template,
                        key="contact",
                        label="联系方式",
                        required=False,
                        sort_order=2,
                    ),
                    CustomerTemplateItem(
                        template=template,
                        key="note",
                        label="客户备注",
                        required=False,
                        sort_order=3,
                    ),
                ]
            )
            ImageTemplateItem.objects.bulk_create(
                [
                    ImageTemplateItem(
                        template=template,
                        key="customer-original",
                        label="客户原图",
                        required=True,
                        min_count=1,
                        sort_order=1,
                        help_text="客户提供的原始图片。",
                    ),
                    ImageTemplateItem(
                        template=template,
                        key="detail",
                        label="细节图",
                        required=False,
                        min_count=0,
                        sort_order=2,
                    ),
                    ImageTemplateItem(
                        template=template,
                        key="reference",
                        label="参考图",
                        required=False,
                        min_count=0,
                        sort_order=3,
                    ),
                ]
            )

        self.stdout.write(self.style.SUCCESS("Demo data is ready. Default PIN is 123456."))
