from django.contrib.sessions.models import Session
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

    def test_second_home_visit_from_same_browser_does_not_increment(self):
        self.client.get(self.home_url)
        self.client.get(self.home_url)
        self.assertEqual(PageView.get_instance().count, 1)

    def test_home_visit_from_different_browser_increments_again(self):
        self.client.get(self.home_url)
        second_client = Client()
        second_client.get(self.home_url)
        self.assertEqual(PageView.get_instance().count, 2)

    def test_home_visit_sets_cookie_without_creating_a_session(self):
        response = self.client.get(self.home_url)
        self.assertEqual(response.cookies["has_visited"].value, "1")
        self.assertEqual(Session.objects.count(), 0)

    def test_home_alias_redirect_is_not_counted(self):
        self.client.get("/home/")
        self.assertEqual(PageView.get_instance().count, 0)

    def test_non_home_path_does_not_increment_counter(self):
        self.client.get(self.about_url)
        self.assertEqual(PageView.get_instance().count, 0)
