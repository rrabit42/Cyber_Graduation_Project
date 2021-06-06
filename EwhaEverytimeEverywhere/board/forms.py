from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'content',)

        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'style': 'width: 100%',
                    'placeholder': '제목을 입력하세요.'}
            ),
            'content': forms.CharField(
                widget=CKEditorUploadingWidget()
            ),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment

        fields = ('comment_textfield',)
        widgets = {
            'comment_textfield': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'cols': 40})
        }

