from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 4, "placeholder": "输入进展，可用 @姓名 通知成员"}),
        }
