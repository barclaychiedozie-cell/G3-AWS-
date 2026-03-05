from django import forms
from .models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text", "pressure_data"]
        widgets = {"text": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["pressure_data"].queryset = user.pressure_data.all()