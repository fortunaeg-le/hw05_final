from django.test import Client, TestCase


class AboutTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_for_about_template(self):
        """Проверяем шаблоны для tech и author"""
        templates_about = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }
        for adress, template in templates_about.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)
