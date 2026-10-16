from unittest.mock import Mock, patch

import requests
from django.test import SimpleTestCase, override_settings

from main.github_client import (
    GitHubAuthError,
    GitHubUpstreamError,
    fetch_contribution_days,
)
from main.heatmap import build_weeks_payload, contribution_level, fetch_heatmap_data


class GitHubClientTests(SimpleTestCase):
    @patch("main.github_client.requests.post")
    def test_fetch_contribution_days_maps_http_errors(self, post_mock):
        cases = ((401, GitHubAuthError), (403, GitHubAuthError), (500, GitHubUpstreamError))
        for status_code, error_class in cases:
            with self.subTest(status_code=status_code):
                response = Mock()
                response.status_code = status_code
                response.headers = {}
                post_mock.return_value = response

                with self.assertRaises(error_class):
                    fetch_contribution_days("gho_token")

    @patch("main.github_client.requests.post")
    def test_fetch_contribution_days_raises_upstream_error_for_rate_limit(self, post_mock):
        response = Mock()
        response.status_code = 403
        response.headers = {"X-RateLimit-Remaining": "0"}
        post_mock.return_value = response

        with self.assertRaises(GitHubUpstreamError):
            fetch_contribution_days("gho_valid")

    @patch("main.github_client.requests.post")
    def test_fetch_contribution_days_raises_upstream_error_for_missing_data(
        self, post_mock
    ):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"data": None}
        post_mock.return_value = response

        with self.assertRaises(GitHubUpstreamError):
            fetch_contribution_days("gho_valid")

    @patch("main.github_client.requests.post")
    def test_fetch_contribution_days_flattens_graphql_weeks(self, post_mock):
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

        login, days = fetch_contribution_days("gho_valid")

        self.assertEqual(login, "PortfolioUser")
        self.assertEqual(
            days,
            [
                {"date": "2026-01-04", "count": 1},
                {"date": "2026-01-05", "count": 3},
                {"date": "2026-01-11", "count": 5},
            ],
        )

    @patch("main.github_client.requests.post", side_effect=requests.Timeout)
    def test_fetch_contribution_days_raises_upstream_error_for_timeout(
        self, _post_mock
    ):
        with self.assertRaises(GitHubUpstreamError):
            fetch_contribution_days("gho_valid")

    @patch("main.github_client.requests.post")
    def test_fetch_contribution_days_raises_auth_error_for_graphql_errors(
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

        with self.assertRaises(GitHubAuthError):
            fetch_contribution_days("gho_invalid")


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

    def test_build_weeks_payload_groups_days_and_total(self):
        weeks, total = build_weeks_payload(
            [
                {"date": "2026-01-05", "count": 3},
                {"date": "2026-01-04", "count": 1},
                {"date": "2026-01-12", "count": 10},
                {"date": "invalid", "count": 99},
            ]
        )

        self.assertEqual(total, 14)
        self.assertEqual(
            weeks,
            [
                {
                    "week_start": "2026-01-04",
                    "days": [
                        {
                            "date": "2026-01-04",
                            "weekday": 0,
                            "count": 1,
                            "level": 1,
                        },
                        {
                            "date": "2026-01-05",
                            "weekday": 1,
                            "count": 3,
                            "level": 2,
                        },
                    ],
                },
                {
                    "week_start": "2026-01-11",
                    "days": [
                        {
                            "date": "2026-01-12",
                            "weekday": 1,
                            "count": 10,
                            "level": 4,
                        }
                    ],
                },
            ],
        )

    @override_settings(GITHUB_HEATMAP_TOKEN="gho_env_token")
    @patch("main.heatmap.fetch_contribution_days")
    def test_fetch_heatmap_data_returns_normalized_payload(self, fetch_days_mock):
        fetch_days_mock.return_value = (
            "PortfolioUser",
            [
                {"date": "2026-01-04", "count": 1},
                {"date": "2026-01-05", "count": 3},
                {"date": "2026-01-12", "count": 10},
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
                        "week_start": "2026-01-04",
                        "days": [
                            {
                                "date": "2026-01-04",
                                "weekday": 0,
                                "count": 1,
                                "level": 1,
                            },
                            {
                                "date": "2026-01-05",
                                "weekday": 1,
                                "count": 3,
                                "level": 2,
                            },
                        ],
                    },
                    {
                        "week_start": "2026-01-11",
                        "days": [
                            {
                                "date": "2026-01-12",
                                "weekday": 1,
                                "count": 10,
                                "level": 4,
                            }
                        ],
                    },
                ],
            },
        )
        fetch_days_mock.assert_called_once_with("gho_env_token")

    @override_settings(GITHUB_HEATMAP_TOKEN="gho_invalid")
    @patch("main.heatmap.fetch_contribution_days", side_effect=GitHubAuthError)
    def test_fetch_heatmap_data_maps_auth_error(self, _fetch_days_mock):
        payload, error = fetch_heatmap_data()

        self.assertIsNone(payload)
        self.assertEqual(error, "Configured GitHub token is invalid or expired.")

    @override_settings(GITHUB_HEATMAP_TOKEN="gho_valid")
    @patch("main.heatmap.fetch_contribution_days", side_effect=GitHubUpstreamError)
    def test_fetch_heatmap_data_maps_upstream_error(self, _fetch_days_mock):
        payload, error = fetch_heatmap_data()

        self.assertIsNone(payload)
        self.assertEqual(error, "Heatmap service is temporarily unavailable.")
