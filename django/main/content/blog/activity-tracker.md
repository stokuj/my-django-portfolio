# Activity Tracker

A web application for tracking physical activity, sharing posts, and generating activity statistics.

## Features

- User registration and authentication (including Google OAuth via `django-allauth`)
- Activity tracking by category and duration
- Social feed with posts, comments, follow/unfollow
- CSV import/export for activities
- Activity reports with Plotly charts
- Profile privacy and account settings

## Use Cases

- As a user, I track my physical activity by creating entries with category and duration.
- As a user, I review my progress by generating charts and activity reports.
- As a user, I share updates by publishing posts and adding comments.
- As a user, I discover other people by searching profiles and following accounts.
- As a user, I keep my data portable by exporting and importing activities via CSV.

## Tech Stack

- Python 3.10
- Django 5
- PostgreSQL
- uv (dependency and environment management)
- Plotly, Pandas, Crispy Forms
- Bootstrap

## How to install

1. Clone the repository:

2. Create PostgreSQL database (name must match `DB_NAME` in `.env`):
```sql
CREATE DATABASE activityDB;
```

3. Create `.env` with your local PostgreSQL credentials.
Look at `.env.example`

4. Install dependencies and run server
```bash
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

## Showcase
User can register on the register page.
<img width="2275" height="1442" alt="activity_chart" src="https://github.com/user-attachments/assets/f1bb348f-d656-46f0-84ec-ede13c7bc4aa" />

User can add new activities with a name, category, and time.
All validations are included
<img width="2275" height="1356" alt="activity_list" src="https://github.com/user-attachments/assets/28f8585a-58ab-41d9-b5c8-75a2cfd41612" />

User can view and generate charts based on his activities. He can download them and upload from csv.
<img width="2275" height="1442" alt="activity_chart" src="https://github.com/user-attachments/assets/a07a0d9f-c4d7-4293-962f-b8e6035417e3" />


## License

MIT License. See `LICENSE`.
This project is for educational purposes. It was built to practice Django web development, PostgreSQL integration, authentication flows, and basic product design patterns.
