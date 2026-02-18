from django.test import Client, TestCase
from django.urls import reverse

from main.models import PageView


class VisitorCountMiddlewareTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.home_url = reverse("home")
        self.about_url = reverse("about")

    def test_first_home_visit_increments_counter(self):
        self.client.get(self.home_url)
        self.assertEqual(PageView.get_instance().count, 1)

    def test_second_home_visit_in_same_session_does_not_increment(self):
        self.client.get(self.home_url)
        self.client.get(self.home_url)
        self.assertEqual(PageView.get_instance().count, 1)

    def test_home_visit_in_different_session_increments_again(self):
        self.client.get(self.home_url)
        second_client = Client()
        second_client.get(self.home_url)
        self.assertEqual(PageView.get_instance().count, 2)

    def test_home_alias_path_is_counted(self):
        self.client.get("/home/")
        self.assertEqual(PageView.get_instance().count, 1)

    def test_non_home_path_does_not_increment_counter(self):
        self.client.get(self.about_url)
        self.assertEqual(PageView.get_instance().count, 0)
