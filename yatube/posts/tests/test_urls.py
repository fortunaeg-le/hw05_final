from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def test_homepage(self):
        guest_client = Client()
        response = guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class URLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='auth_1')
        cls.user2 = User.objects.create_user(username='auth_2')
        cls.group = Group.objects.create(
            title='Тестовое имя',
            slug='thegroup'
        )
        cls.post = Post.objects.create(
            author=cls.user2,
            text='Тестовый текст поста',
            group=cls.group,
            pk=1
        )
        cls.urls = [
            '/',
            '/group/thegroup/',
            '/profile/auth_1/',
            f'/posts/{cls.post.pk}/',
        ]

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user1)

        self.postauthor_client = Client()
        self.postauthor_client.force_login(self.user2)

    def test_template_for_guest_user(self):
        """Тест доступности страниц для неавторизованного юзера"""
        for adress in URLTest.urls:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_urls_for_auth_user(self):
        """Тест доступности страниц для авторизованного пользователя"""
        for adress in URLTest.urls:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexp_for_guest_user(self):
        """Тест доступности несуществующей страницы для неавторизов юзера"""
        response = self.guest_client.get('/test_pr/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_unexp_for_authorizadet_user(self):
        """Тест доступности несуществующей страницы для авторизован юзера"""
        response = self.authorized_client.get('/test_pr/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_edit_for_author(self):
        """Проверяем возможность изменения поста для автора"""
        response = self.postauthor_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_for_guest_user(self):
        """Тест redirect create для гостевого юзера"""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, ('/auth/login/?next=/create/'))

    def test_edit_for_authorized_user(self):
        """Тест редиректа для зареганого юзера"""
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(response, (f'/posts/{self.post.id}/'))

    def test_template_for_authorizade_user(self):
        """Проверяем URL приложения posts"""
        templates_url_name = {
            '/': 'posts/index.html',
            '/group/thegroup/': 'posts/group_list.html',
            '/profile/auth_1/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
        }
        for adress, template in templates_url_name.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_template_for_author(self):
        """Проверяем шаблон изменения для автора поста"""
        response = self.postauthor_client.get(f'/posts/{self.post.id}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')
