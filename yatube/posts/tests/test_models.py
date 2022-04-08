from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='auth'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тустовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_name(self):
        """Проверяем, что у модели Group корректно работает __str__"""
        group = str(PostModelTest.group.__str__())
        self.assertEqual(self.group.title, group)

    def test_models_have_correct_object_name_1(self):
        """Проверяем, что у модели Post корректно работает __str__"""
        post = str(PostModelTest.post)
        self.assertEqual(self.post.text[:15], post)

    def test_models_have_correct_object_name_3(self):
        """Проверяемб что у модели User корректно работает __str__"""
        user = str(PostModelTest.user)
        self.assertEqual(self.user.__str__(), user)
