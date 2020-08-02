from django.test import Client, TestCase
from django.urls import reverse
from urllib.parse import urljoin
from django.core.cache import cache
from io import BytesIO
from PIL import Image

import mock

from django.core.files import File
from .models import Post, User, Group, Follow, Comment


class HomeWork04Test(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="Roman", email="honor.s@skybed.com")
        self.client_auth = Client()
        self.client_auth.force_login(self.user)
        self.client_un_auth = Client()
        self.group = Group.objects.create(
            title="Bang",
            slug="ang"
        )

    def asserts(self, url, group, text, author):
        response = self.client_auth.get(url)
        if 'paginator' in response.context:
            posts = response.context['paginator'].object_list[0]
        else:
            posts = response.context["post"]
        self.assertEqual(posts.text, text)
        self.assertEqual(posts.author, author)
        self.assertEqual(posts.group, group)

    def test_profile(self):
        response = self.client.get(reverse('profile',
                                           kwargs=dict(
                                               username=self.user.username)))
        self.assertEqual(response.status_code, 200)

    def test_new_post(self):
        response = self.client_auth.post(reverse('new_post'),
                                         data={'text': 'text',
                                               'group': self.group.id,
                                               'author': self.user},
                                         follow=True)
        self.assertEqual(response.status_code, 200)
        posts_new = Post.objects.all()
        self.assertEqual(posts_new.first().text, 'text')
        self.assertEqual(posts_new.count(), 1)
        self.assertEqual(posts_new.first().author, self.user)
        self.assertEqual(posts_new.first().group, self.group)

    def test_new_post_not_authorized(self):
        response = self.client_un_auth.post(reverse('new_post'),
                                            data={'text': 'damn, boy'})
        url = urljoin(reverse('login'), '?next=' + reverse('new_post'))
        self.assertEquals(Post.objects.count(), 0)
        self.assertRedirects(response, url)

    def test_post_show(self):
        post = Post.objects.create(text='text', author=self.user,
                                   group=self.group)
        for url in (
                reverse("index"),
                reverse("profile", kwargs={"username": self.user.username}),
                reverse("post", kwargs={
                    "username": self.user.username,
                    "post_id": post.id}
                        )

        ):
            self.asserts(url, self.group, post.text, self.user)

    def test_post_edit(self):
        post = Post.objects.create(text='text', author=self.user,
                                   group=self.group)
        new_group = Group.objects.create(
            title="Bank",
            slug="ank"
        )
        post_text = "edit_text"
        response = self.client_auth.post(
            reverse(
                "post_edit",
                kwargs={
                    "username": self.user.username,
                    "post_id": post.id,
                }
            ), follow=True,
            data={'text': post_text, 'group': new_group.id}
        )
        self.assertEqual(response.status_code, 200)
        posts_new = Post.objects.first()
        for url in (
                reverse("index"),
                reverse("profile", kwargs={"username": self.user.username}),
                reverse("post", kwargs={
                    "username": self.user.username,
                    "post_id": post.id}
                        ),
                reverse('group_posts', kwargs={'slug': new_group.slug})

        ):
            self.asserts(url, new_group, post_text, self.user)


class Hw05Test(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="Roman", email="honor.s@skybed.com")
        self.client_auth = Client()
        self.client_auth.force_login(self.user)
        self.client_un_auth = Client()
        self.group = Group.objects.create(
            title="Bang",
            slug="ang"
        )

    @staticmethod
    def create_test_image_file():
        file = BytesIO()
        image = Image.new('RGBA', size=(100, 100), color=(155, 0, 0))
        image.save(file, 'png')
        file.name = 'test.png'
        file.seek(0)
        return file

    def test_404(self):
        response = self.client.get('/404/')
        self.assertEqual(response.status_code, 404)

    def test_img_upload_success(self):
        file = self.create_test_image_file()
        post = self.client_auth.post(
            reverse('new_post'),
            data={
                'author': self.user,
                'text': 'post text with image',
                'group': self.group.id,
                'image': file
            },
            follow=True)
        self.assertEqual(post.status_code, 200)
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        urls = [
            reverse('index'),
            reverse('post', kwargs={'username': self.user.username,
                                    'post_id': post.id}),
            reverse('profile', kwargs={'username': post.author}),
            reverse('group_posts', kwargs={'slug': 'ang'}),
        ]
        for url in urls:
            cache.clear()
            response = self.client_auth.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '<img')

    def test_upload_wrong_file(self):
        file_mock = mock.MagicMock(spec=File, name='wrong.txt')
        response = self.client_auth.post(reverse('new_post'),
                                         {'text': 'post with image',
                                          'group': self.group.id,
                                          'image': file_mock},
                                         follow=True)
        self.assertFormError(response, form='form', field='image',
                             errors='Загрузите правильное изображение.'
                                    ' Файл, который вы'
                                    ' загрузили, поврежден или не'
                                    ' является изображением.')

    def test_cache(self):
        self.client_auth.post(reverse('new_post'),
                              data={'text': 'text',
                                    'group': self.group.id,
                                    'author': self.user},
                              follow=True)
        posts_new = Post.objects.all()
        self.assertEqual(posts_new.first().text, 'text')

        response = self.client_auth.get(reverse('index'))
        text = Post.objects.filter(text='text')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, text)

    def test_authorized_user_comment(self):
        post = Post.objects.create(text='text', author=self.user,
                                   group=self.group)
        response = self.client_un_auth.post(
            reverse(
                "add_comment",
                kwargs={
                    "username": self.user.username,
                    "post_id": post.id,
                }
            ), follow=True,
            data={'text': 'blah', 'group': self.group.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 0)

        response = self.client_auth.post(
            reverse(
                "add_comment",
                kwargs={
                    "username": self.user.username,
                    "post_id": post.id,
                }
            ), follow=True,
            data={'text': 'blah blah', 'group': self.group.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)


class FollowTest(TestCase):
    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create_user(
            username="follower", email="honor@skynet.com")
        self.user_following = User.objects.create_user(
            username="following", email="blablabla@mail.ru")
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_follow_unfollow(self):
        no_follow = Follow.objects.all().count()
        self.assertEqual(no_follow, 0)
        self.client_auth_follower.get(
            reverse(
                "profile_follow",
                kwargs={
                    "username": self.user_following.username,
                },
            )
        )
        with_follow = Follow.objects.all().count()
        self.assertEqual(with_follow, 1)

        self.client_auth_follower.get(
            reverse(
                "profile_unfollow",
                kwargs={
                    "username": self.user_following.username,
                },
            )
        )
        with_no_follow = Follow.objects.all().count()
        self.assertEqual(with_no_follow, 0)

    def test_new_post_follow(self):
        self.client_auth_following.post(reverse('new_post'),
                                        data={'text': 'text',
                                              'author': self.client_auth_following},
                                        follow=True)
        response = self.client_auth_follower.get(
            reverse(
                "follow_index"))
        posts = response.context['paginator'].object_list
        self.assertFalse(posts, 'text')

        self.client_auth_follower.get(
            reverse(
                "profile_follow",
                kwargs={
                    "username": self.user_following.username,
                },
            )
        )
        response = self.client_auth_follower.get(
            reverse(
                "follow_index"))
        posts = response.context['paginator'].object_list[0]
        self.assertEqual(posts.text, 'text')
        self.assertEqual(posts.author.username, self.user_following.username)
