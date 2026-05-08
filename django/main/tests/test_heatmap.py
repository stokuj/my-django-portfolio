from unittest.mock import Mock
from unittest.mock import patch

import requests
from django.test import SimpleTestCase
from django.test import override_settings

from main.github_client import GitHubAuthError
from main.github_client import GitHubUpstreamError
from main.github_client import fetch_authenticated_user
from main.github_client import fetch_contribution_days
from main.heatmap import build_weeks_payload
from main.heatmap import contribution_level
from main.heatmap import fetch_heatmap_data


class GitHubClientTests(SimpleTestCase):
    @patch("main.github_client.requests.get")
    def test_fetch_authenticated_user_returns_login(self, get_mock):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"id": 123, "login": "PortfolioUser"}
        get_mock.return_value = response

        payload = fetch_authenticated_user("gho_valid")

        self.assertEqual(payload, {"id": 123, "login": "PortfolioUser"})

    @patch("main.github_client.requests.get")
    def test_fetch_authenticated_user_raises_auth_error_for_401(self, get_mock):
        response = Mock()
        response.status_code = 401
        get_mock.return_value = response

        with self.assertRaises(GitHubAuthError):
            fetch_authenticated_user("gho_invalid")

    @patch("main.github_client.requests.post")
    def test_fetch_contribution_days_flattens_graphql_weeks(self, post_mock):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "data": {
                "user": {
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

        payload = fetch_contribution_days("portfolio-user", "gho_valid")

        self.assertEqual(
            payload,
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
            fetch_contribution_days("portfolio-user", "gho_valid")

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
            fetch_contribution_days("PortfolioUser", "gho_invalid")


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
    @patch("main.heatmap.fetch_authenticated_user")
    def test_fetch_heatmap_data_returns_normalized_payload(
        self,
        fetch_user_mock,
        fetch_days_mock,
    ):
        fetch_user_mock.return_value = {"id": 123, "login": "PortfolioUser"}
        fetch_days_mock.return_value = [
            {"date": "2026-01-04", "count": 1},
            {"date": "2026-01-05", "count": 3},
            {"date": "2026-01-12", "count": 10},
        ]

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
        fetch_user_mock.assert_called_once_with("gho_env_token")
        fetch_days_mock.assert_called_once_with("PortfolioUser", "gho_env_token")

    @override_settings(GITHUB_HEATMAP_TOKEN="gho_invalid")
    @patch("main.heatmap.fetch_authenticated_user", side_effect=GitHubAuthError)
    def test_fetch_heatmap_data_maps_auth_error(self, _fetch_user_mock):
        payload, error = fetch_heatmap_data()

        self.assertIsNone(payload)
        self.assertEqual(error, "Configured GitHub token is invalid or expired.")

    @override_settings(GITHUB_HEATMAP_TOKEN="gho_invalid")
    @patch("main.heatmap.fetch_contribution_days", side_effect=GitHubAuthError)
    @patch("main.heatmap.fetch_authenticated_user")
    def test_fetch_heatmap_data_maps_graphql_auth_error(
        self,
        fetch_user_mock,
        _fetch_days_mock,
    ):
        fetch_user_mock.return_value = {"id": 123, "login": "PortfolioUser"}

        payload, error = fetch_heatmap_data()

        self.assertIsNone(payload)
        self.assertEqual(error, "Configured GitHub token is invalid or expired.")
