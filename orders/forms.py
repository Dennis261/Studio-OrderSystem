from django import forms

from .models import CustomerTemplateItem, ImageTemplate, ImageTemplateItem, StatusOption, make_template_key


class WorkOrderForm(forms.Form):
    status = forms.ModelChoiceField(
        label="状态",
        queryset=StatusOption.objects.none(),
        required=False,
    )

    def __init__(self, *args, template_snapshot=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.template_snapshot = template_snapshot or {}
        self.fields["status"].queryset = StatusOption.objects.filter(is_active=True)
        for item in self.customer_fields:
            self.fields[f"customer_{item['key']}"] = forms.CharField(
                label=item["label"],
                required=item.get("required", False),
                help_text=item.get("help_text", ""),
                widget=forms.TextInput,
            )

    @property
    def customer_fields(self):
        return self.template_snapshot.get("customer_fields", [])

    def customer_data(self):
        data = {}
        for item in self.customer_fields:
            data[item["key"]] = self.cleaned_data.get(f"customer_{item['key']}", "")
        return data


class StatusOptionForm(forms.ModelForm):
    class Meta:
        model = StatusOption
        fields = ["name", "sort_order", "is_active"]


class ImageTemplateForm(forms.Form):
    name = forms.CharField(label="模板名称", max_length=80)

    def clean(self):
        cleaned = super().clean()
        if self.is_bound:
            cleaned["customer_rows"] = self._parse_customer_rows()
            cleaned["image_rows"] = self._parse_image_rows()
            if not cleaned["customer_rows"]:
                raise forms.ValidationError("至少需要一个客户信息字段。")
            if not cleaned["image_rows"]:
                raise forms.ValidationError("至少需要一个图片项。")
        return cleaned

    def save(self, member):
        next_version = (ImageTemplate.objects.order_by("-version").first().version + 1) if ImageTemplate.objects.exists() else 1
        template = ImageTemplate.objects.create(
            name=self.cleaned_data["name"],
            version=next_version,
            created_by=member,
        )
        self._create_rows(template, CustomerTemplateItem, self.cleaned_data["customer_rows"])
        self._create_rows(template, ImageTemplateItem, self.cleaned_data["image_rows"])
        template.publish()
        return template

    def _parse_customer_rows(self):
        rows = []
        for index in self._indices("customer"):
            label = self.data.get(f"customer_label_{index}", "").strip()
            if not label:
                continue
            rows.append(
                {
                    "label": label,
                    "required": self.data.get(f"customer_required_{index}") == "on",
                    "help_text": self.data.get(f"customer_help_{index}", "").strip(),
                    "sort_order": len(rows) + 1,
                }
            )
        return rows

    def _parse_image_rows(self):
        rows = []
        for index in self._indices("image"):
            label = self.data.get(f"image_label_{index}", "").strip()
            if not label:
                continue
            try:
                min_count = int(self.data.get(f"image_min_count_{index}", "0") or 0)
            except ValueError as exc:
                raise forms.ValidationError(f"图片项“{label}”的张数必须是数字。") from exc
            if min_count < 0:
                raise forms.ValidationError(f"图片项“{label}”的张数不能小于 0。")
            rows.append(
                {
                    "label": label,
                    "required": self.data.get(f"image_required_{index}") == "on",
                    "min_count": min_count,
                    "help_text": self.data.get(f"image_help_{index}", "").strip(),
                    "sort_order": len(rows) + 1,
                }
            )
        return rows

    def _indices(self, prefix):
        raw_indices = self.data.getlist(f"{prefix}_indices")
        return raw_indices or [str(index) for index in range(1, 8)]

    def _create_rows(self, template, model, rows):
        used_keys = set()
        for index, row in enumerate(rows, start=1):
            key = make_template_key(row["label"], index)
            original_key = key
            suffix = 2
            while key in used_keys:
                key = f"{original_key}-{suffix}"
                suffix += 1
            used_keys.add(key)
            model.objects.create(template=template, key=key, **row)
