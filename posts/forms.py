from django.forms import ModelForm

from .models import Post, Comment


class PostForm(ModelForm):

    class Meta:
        help_texts = {
            'group': "Выберите группу для поста",
            'text': "Введите текст поста"
        }
        labels = {
            'group': "Группа",
            'text': "Текст"
        }
        model = Post
        fields = ['group', 'text', 'image']


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text', ]
