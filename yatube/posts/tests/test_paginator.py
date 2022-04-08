from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PaginatorTest(TestCase):
    """Проверяем paginator шаблонов index, group_list, profile"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testauth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = [
            Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост- {i}',
                group=cls.group
            )
            for i in range(14)
        ]

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator_for_index(self):
        """Тестируем paginator для индекса"""
        response = self.authorized_client.get(reverse('posts:index'))
        response_1 = self.authorized_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 10)
        self.assertEqual(len(response_1.context['page_obj']), 4)

    def test_paginator_for_group_list(self):
        """Тестируем paginator для group_list"""
        url = reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        response = self.authorized_client.get(url)
        response_1 = self.authorized_client.get(url + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 10)
        self.assertEqual(len(response_1.context['page_obj']), 4)

    def test_paginator_for_profile(self):
        """Проверяем paginator для profile"""
        url = reverse('posts:profile', kwargs={'username': 'testauth'})
        response = self.authorized_client.get(url)
        response_1 = self.authorized_client.get(url + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 10)
        self.assertEqual(len(response_1.context['page_obj']), 4)
