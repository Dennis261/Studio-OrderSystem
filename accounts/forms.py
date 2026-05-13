from django import forms

from .models import Member


class MemberLoginForm(forms.Form):
    member = forms.ModelChoiceField(
        label="姓名",
        queryset=Member.objects.none(),
        empty_label="请选择姓名",
    )
    pin = forms.CharField(label="口令", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["member"].queryset = Member.objects.filter(is_active=True)

    def clean(self):
        cleaned = super().clean()
        member = cleaned.get("member")
        pin = cleaned.get("pin")
        if member and pin and not member.check_pin(pin):
            raise forms.ValidationError("姓名或口令不正确。")
        return cleaned


class MemberForm(forms.ModelForm):
    pin = forms.CharField(
        label="新口令",
        required=False,
        widget=forms.PasswordInput,
        help_text="新增成员必填；编辑时留空表示不修改。",
    )

    class Meta:
        model = Member
        fields = ["name", "is_admin", "is_active"]

    def save(self, commit=True):
        member = super().save(commit=False)
        pin = self.cleaned_data.get("pin")
        if pin:
            member.set_pin(pin)
        if commit:
            member.save()
            self.save_m2m()
        return member
