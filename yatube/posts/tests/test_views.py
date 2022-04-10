import shutil
import tempfile

from django.core.cache import cache
from django.conf import settings
from django import forms
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, Comment, Follow

User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug'
        )
        cls.user = User.objects.create_user(
            username='testauth'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.gif_name = 'small.gif'
        cls.uploaded = SimpleUploadedFile(
            name=cls.gif_name,
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded,
            pk=1
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый коммент'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()

        self.user = User.objects.get(username='testauth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_used_correct_template(self):
        """Проверяем соответствия шаблонов и URL"""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test_slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'testauth'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': '1'}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}
            ): 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_for_index_context(self):
        """Проверяем context индекса"""
        response = self.authorized_client.get(reverse('posts:index'))
        objects = response.context['page_obj'][0]
        posts = Post.objects.all()[0]
        self.assertEqual(objects, posts)

    def test_for_grouplist_context(self):
        """Проверяем context у group_list"""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            )
        )
        expected_objects = response.context['group']
        task_title = expected_objects.title
        task_slug = expected_objects.slug
        self.assertEqual(task_title, 'Тестовый заголовок')
        self.assertEqual(task_slug, self.group.slug)

    def test_for_profile_context(self):
        """Проверяем context у профиля"""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        expected_objects = response.context['author']
        task_author = expected_objects.username
        self.assertEqual(task_author, self.user.username)

    def test_for_postdetail_context(self):
        """Проверяем context у post_detail"""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            )
        )
        self.assertEqual(response.context['post'].author, ViewTest.post.author)
        self.assertEqual(response.context['post'].text, 'Тестовый текст')
        self.assertEqual(
            response.context['post'].group.title,
            'Тестовый заголовок'
        )
        self.assertEqual(
            response.context['comments'][:1][0].text,
            ViewTest.comment.text
        )
        self.assertEqual(
            response.context['comments'][:1][0].author.id,
            ViewTest.user.id
        )

    def test_for_create_context(self):
        """Проверяем формы и context в create"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            form_field = response.context.get('form').fields.get(value)
            self.assertIsInstance(form_field, expected)

    def test_for_postedit_context(self):
        """Проверяем context у форм изменения поста"""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            form_field = response.context.get('form').fields.get(value)
            self.assertIsInstance(form_field, expected)

    def test_post_show_on_template(self):
        """Пост появляется в index, group_list, profile"""
        views_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        ]
        for view_name in views_names:
            with self.subTest(veiw_name=view_name):
                response = self.authorized_client.get(view_name)
                self.assertIn(
                    self.post, response.context['page_obj'].object_list
                )

    def test_index_cache(self):
        """Проверяем кэширование шаблона индекс"""
        index_cache = Post.objects.create(
            text='Проверочный текст',
            author=self.user
        )
        response = self.authorized_client.get(reverse('posts:index'))
        content_1 = response.content
        index_cache.delete()
        new_response = self.authorized_client.get(reverse('posts:index'))
        new_content = new_response.content
        self.assertEqual(content_1, new_content)
        cache.clear()
        response_2 = self.authorized_client.get(reverse('posts:index'))
        content_2 = response_2.content
        self.assertNotEqual(content_1, content_2)

    def test_following_to_author(self):
        """Проверка возможности подписываться"""
        follow_user = User.objects.create_user(username='follow')
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': follow_user.username}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=follow_user
            ).exists()
        )

    def test_unfollowing_from_author(self):
        """Проверка возможности отписаться"""
        follow_user = User.objects.create(
            username='follow'
        )
        Follow.objects.create(
            user=self.user,
            author=follow_user
        )
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': follow_user.username}
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=follow_user,
            ).exists()
        )

    def test_posts_for_folower_in_follow_index(self):
        """Проверяем выводимость постов"""
        follower = User.objects.create_user(username='follower')
        author = User.objects.create_user(username='author')

        follower_client = Client()
        follower_client.force_login(follower)

        post = Post.objects.create(
            text='Текст автора',
            author=author
        )

        Follow.objects.create(
            author=author,
            user=follower
        )

        response = follower_client.get(
            reverse(
                'posts:follow_index'
            )
        )
        self.assertEqual(
            response.context['page_obj'][0].pk,
            post.pk
        )

    def test_posts_for_unfollow_in_follow_index(self):
        """Тестируем, что посты у неподписчиков не выводяться"""
        user = User.objects.create_user(username='user')
        follower = User.objects.create_user(username='follower')
        author = User.objects.create_user(username='author')

        follower_client = Client()
        follower_client.force_login(follower)
        authorized_client = Client()
        authorized_client.force_login(user)
        Post.objects.create(
            text='Текст автора',
            author=author
        )

        Follow.objects.create(
            author=author,
            user=follower
        )
        response = authorized_client.get(
            reverse(
                'posts:follow_index'
            )
        )
        self.assertFalse(response.context['page_obj'])
