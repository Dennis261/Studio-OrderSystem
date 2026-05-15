from django.core.management.base import BaseCommand

from accounts.models import Member
from orders.models import CustomerTemplateItem, ImageTemplate, ImageTemplateItem, StatusOption, WorkOrder


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

        tag_names = ["新建", "建模中", "待确认", "待生产", "生产中", "已发货", "已完成", "售后"]
        tags = {}
        for index, name in enumerate(tag_names, start=1):
            tag, _ = StatusOption.objects.get_or_create(name=name, defaults={"sort_order": index})
            tags[name] = tag

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

        if not WorkOrder.objects.exists():
            template = ImageTemplate.active()
            admin = Member.objects.filter(is_admin=True).first()
            creator = Member.objects.filter(name="客服小王").first() or admin
            sample_orders = [
                {
                    "customer": "张三",
                    "contact": "13800000001",
                    "note": "常规新单，等待建模。",
                    "tags": ["新建"],
                    "is_archived": False,
                },
                {
                    "customer": "李四",
                    "contact": "13800000002",
                    "note": "建模中，同时等待客户确认细节。",
                    "tags": ["建模中", "待确认"],
                    "is_archived": False,
                },
                {
                    "customer": "王五",
                    "contact": "13800000003",
                    "note": "已经发货，后续可能进入售后。",
                    "tags": ["已发货"],
                    "is_archived": False,
                },
                {
                    "customer": "赵六",
                    "contact": "13800000004",
                    "note": "已完成并归档，仅默认列表隐藏。",
                    "tags": ["已完成"],
                    "is_archived": True,
                },
                {
                    "customer": "钱七",
                    "contact": "13800000005",
                    "note": "已完成后产生售后跟进。",
                    "tags": ["已完成", "售后"],
                    "is_archived": True,
                },
            ]
            for sample in sample_orders:
                order = WorkOrder.objects.create(
                    customer_name=sample["customer"],
                    customer_contact=sample["contact"],
                    customer_note=sample["note"],
                    customer_data={
                        "customer-name": sample["customer"],
                        "contact": sample["contact"],
                        "note": sample["note"],
                    },
                    is_archived=sample["is_archived"],
                    creator=creator,
                    template_snapshot=template.to_snapshot() if template else {},
                )
                order.tags.set(tags[name] for name in sample["tags"])

        self.stdout.write(self.style.SUCCESS("Demo data is ready. Default PIN is 123456."))
