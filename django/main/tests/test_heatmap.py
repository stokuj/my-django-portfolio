from unittest.mock import Mock, patch

import requests
from django.test import SimpleTestCase, override_settings

from main.github_client import (
    GitHubAuthError,
    GitHubUpstreamError,
    fetch_contribution_weeks,
)
from main.heatmap import contribution_level, fetch_heatmap_data


class GitHubClientTests(SimpleTestCase):
    @patch("main.github_client.requests.post")
    def test_fetch_contribution_weeks_maps_http_errors(self, post_mock):
        cases = ((401, GitHubAuthError), (403, GitHubAuthError), (500, GitHubUpstreamError))
        for status_code, error_class in cases:
            with self.subTest(status_code=status_code):
                response = Mock()
                response.status_code = status_code
                response.headers = {}
                post_mock.return_value = response

                with self.assertRaises(error_class):
                    fetch_contribution_weeks("gho_token")

    @patch("main.github_client.requests.post")
    def test_fetch_contribution_weeks_raises_upstream_error_for_rate_limit(self, post_mock):
        response = Mock()
        response.status_code = 403
        response.headers = {"X-RateLimit-Remaining": "0"}
        post_mock.return_value = response

        with self.assertRaises(GitHubUpstreamError):
            fetch_contribution_weeks("gho_valid")

    @patch("main.github_client.requests.post")
    def test_fetch_contribution_weeks_raises_upstream_error_for_missing_data(
        self, post_mock
    ):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"data": None}
        post_mock.return_value = response

        with self.assertRaises(GitHubUpstreamError):
            fetch_contribution_weeks("gho_valid")

    @patch("main.github_client.requests.post")
    def test_fetch_contribution_weeks_keeps_graphql_weeks(self, post_mock):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "data": {
                "viewer": {
                    "login": "PortfolioUser",
                    "contributionsCollection": {
                        "contributionCalendar": {
                            "weeks": [
                                {
                                    "contributionDays": [
                                        {
                                            "date": "2026-01-04",
                                            "contributionCount": 1,
                                        },
                                        {
                                            "date": "2026-01-05",
                                            "contributionCount": 3,
                                        },
                                    ]
                                },
                                {
                                    "contributionDays": [
                                        {
                                            "date": "2026-01-11",
                                            "contributionCount": 5,
                                        }
                                    ]
                                },
                            ]
                        }
                    }
                }
            }
        }
        post_mock.return_value = response

        login, weeks = fetch_contribution_weeks("gho_valid")

        self.assertEqual(login, "PortfolioUser")
        self.assertEqual(
            weeks,
            [
                [
                    {"date": "2026-01-04", "count": 1},
                    {"date": "2026-01-05", "count": 3},
                ],
                [{"date": "2026-01-11", "count": 5}],
            ],
        )

    @patch("main.github_client.requests.post", side_effect=requests.Timeout)
    def test_fetch_contribution_weeks_raises_upstream_error_for_timeout(
        self, _post_mock
    ):
        with self.assertRaises(GitHubUpstreamError):
            fetch_contribution_weeks("gho_valid")

    @patch("main.github_client.requests.post")
    def test_fetch_contribution_weeks_raises_upstream_error_for_graphql_errors(
        self, post_mock
    ):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "errors": [
                {
                    "type": "FORBIDDEN",
                    "message": "Resource not accessible by personal access token",
                }
            ]
        }
        post_mock.return_value = response

        with self.assertRaises(GitHubUpstreamError):
            fetch_contribution_weeks("gho_valid")


class HeatmapHelpersTests(SimpleTestCase):
    def test_contribution_level_thresholds(self):
        self.assertEqual(contribution_level(0), 0)
        self.assertEqual(contribution_level(1), 1)
        self.assertEqual(contribution_level(2), 1)
        self.assertEqual(contribution_level(3), 2)
        self.assertEqual(contribution_level(5), 2)
        self.assertEqual(contribution_level(6), 3)
        self.assertEqual(contribution_level(9), 3)
        self.assertEqual(contribution_level(10), 4)

    @override_settings(GITHUB_HEATMAP_TOKEN="gho_env_token")
    @patch("main.heatmap.fetch_contribution_weeks")
    def test_fetch_heatmap_data_returns_normalized_payload(self, fetch_weeks_mock):
        fetch_weeks_mock.return_value = (
            "PortfolioUser",
            [
                [
                    {"date": "2026-01-04", "count": 1},
                    {"date": "2026-01-05", "count": 3},
                ],
                [{"date": "2026-01-12", "count": 10}],
            ],
        )

        payload, error = fetch_heatmap_data()

        self.assertIsNone(error)
        self.assertEqual(
            payload,
            {
                "username": "PortfolioUser",
                "total": 14,
                "weeks": [
                    {
                        "days": [
                            {"date": "2026-01-04", "count": 1, "level": 1},
                            {"date": "2026-01-05", "count": 3, "level": 2},
                        ]
                    },
                    {"days": [{"date": "2026-01-12", "count": 10, "level": 4}]},
                ],
            },
        )
        fetch_weeks_mock.assert_called_once_with("gho_env_token")

    @override_settings(GITHUB_HEATMAP_TOKEN="gho_invalid")
    @patch("main.heatmap.fetch_contribution_weeks", side_effect=GitHubAuthError)
    def test_fetch_heatmap_data_maps_auth_error(self, _fetch_weeks_mock):
        payload, error = fetch_heatmap_data()

        self.assertIsNone(payload)
        self.assertEqual(error, "Configured GitHub token is invalid or expired.")

    @override_settings(GITHUB_HEATMAP_TOKEN="gho_valid")
    @patch("main.heatmap.fetch_contribution_weeks", side_effect=GitHubUpstreamError)
    def test_fetch_heatmap_data_maps_upstream_error(self, _fetch_weeks_mock):
        payload, error = fetch_heatmap_data()

        self.assertIsNone(payload)
        self.assertEqual(error, "Heatmap service is temporarily unavailable.")
