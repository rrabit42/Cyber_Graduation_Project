from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.urls import reverse

from accounts.models import User


class Post(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    content = RichTextUploadingField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    hit = models.PositiveIntegerField(default=0)

    @property
    def update_counter(self):
        self.hit = self.hit + 1
        self.save()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('board:post_detail', kwargs={'pk': self.pk})

    class Meta:
        permissions = [
            ['can_view_goldpage','Can view goldpage'],
        ]


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, related_name='comments')
    comment_created = models.DateTimeField(auto_now_add=True)
    comment_textfield = models.CharField(max_length=200)
    comment_writer = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['id']