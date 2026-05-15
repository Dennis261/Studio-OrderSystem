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

        tag_names = [
            "排单",
            "建模中",
            "建模待修改",
            "小头生产",
            "大头生产",
            "小头排妆",
            "大头排妆",
            "大头小头分别在化妆",
            "正在排假发",
            "正在假发造型",
            "大小头发货",
            "没买假发",
            "已买假发",
            "道具生产中",
            "排道具",
            "道具制作中",
            "没有道具",
            "道具完成",
            "小头发货",
            "大头发货",
            "没做发色确认卡",
            "已做发色确认卡",
            "发色确认卡确认",
            "客户已支付尾款",
            "待发货大头",
            "已发货",
        ]
        tags = {}
        for index, name in enumerate(tag_names, start=1):
            tag, _ = StatusOption.objects.update_or_create(
                name=name,
                defaults={"sort_order": index, "is_active": True},
            )
            tags[name] = tag

        if not ImageTemplate.objects.exists():
            admin = Member.objects.filter(is_admin=True).first()
            template = ImageTemplate.objects.create(
                name="角色头模订单模板",
                version=1,
                is_active=True,
                created_by=admin,
            )
            CustomerTemplateItem.objects.bulk_create(
                [
                    CustomerTemplateItem(
                        template=template,
                        key="role-source",
                        label="角色作品来源",
                        required=True,
                        sort_order=1,
                    ),
                    CustomerTemplateItem(
                        template=template,
                        key="role-name",
                        label="角色名字",
                        required=True,
                        sort_order=2,
                    ),
                    CustomerTemplateItem(
                        template=template,
                        key="customer-height",
                        label="客户身高",
                        required=True,
                        sort_order=3,
                    ),
                    CustomerTemplateItem(
                        template=template,
                        key="customer-weight",
                        label="客户体重",
                        required=True,
                        sort_order=4,
                    ),
                    CustomerTemplateItem(
                        template=template,
                        key="eye-height",
                        label="客户眼高",
                        required=True,
                        sort_order=5,
                    ),
                    CustomerTemplateItem(
                        template=template,
                        key="head-circumference",
                        label="客户头围",
                        required=True,
                        sort_order=6,
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
            sample_orders = [
                {
                    "role_source": "原神",
                    "role_name": "芙宁娜",
                    "height": "165cm",
                    "weight": "50kg",
                    "eye_height": "153cm",
                    "head_circumference": "55cm",
                    "tags": ["排单", "已买假发", "没有道具"],
                    "is_archived": False,
                },
                {
                    "role_source": "崩坏：星穹铁道",
                    "role_name": "卡芙卡",
                    "height": "172cm",
                    "weight": "56kg",
                    "eye_height": "160cm",
                    "head_circumference": "56cm",
                    "tags": ["建模中", "已做发色确认卡"],
                    "is_archived": False,
                },
                {
                    "role_source": "明日方舟",
                    "role_name": "德克萨斯",
                    "height": "168cm",
                    "weight": "52kg",
                    "eye_height": "156cm",
                    "head_circumference": "55.5cm",
                    "tags": ["小头生产", "大头生产", "排道具"],
                    "is_archived": False,
                },
                {
                    "role_source": "阴阳师",
                    "role_name": "不知火",
                    "height": "160cm",
                    "weight": "48kg",
                    "eye_height": "148cm",
                    "head_circumference": "54cm",
                    "tags": ["大头小头分别在化妆", "正在排假发"],
                    "is_archived": False,
                },
                {
                    "role_source": "王者荣耀",
                    "role_name": "貂蝉",
                    "height": "166cm",
                    "weight": "51kg",
                    "eye_height": "154cm",
                    "head_circumference": "55cm",
                    "tags": ["客户已支付尾款", "待发货大头"],
                    "is_archived": False,
                },
                {
                    "role_source": "VOCALOID",
                    "role_name": "初音未来",
                    "height": "158cm",
                    "weight": "45kg",
                    "eye_height": "146cm",
                    "head_circumference": "54cm",
                    "tags": ["已发货"],
                    "is_archived": True,
                },
            ]
            for sample in sample_orders:
                order = WorkOrder.objects.create(
                    customer_name=sample["role_name"],
                    customer_note=f"{sample['role_source']} · {sample['role_name']}",
                    customer_data={
                        "role-source": sample["role_source"],
                        "role-name": sample["role_name"],
                        "customer-height": sample["height"],
                        "customer-weight": sample["weight"],
                        "eye-height": sample["eye_height"],
                        "head-circumference": sample["head_circumference"],
                    },
                    is_archived=sample["is_archived"],
                    template_snapshot=template.to_snapshot() if template else {},
                )
                order.tags.set(tags[name] for name in sample["tags"])

        self.stdout.write(self.style.SUCCESS("Demo data is ready. Default PIN is 123456."))
