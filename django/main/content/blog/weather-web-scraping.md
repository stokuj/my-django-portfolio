# Weather Web Scraping

A desktop weather monitoring app that collects current observations from IMGW, stores them in PostgreSQL, and visualizes trends with interactive Plotly charts.

## Features
- Fetches weather data from IMGW Synop endpoint.
- Stores records in PostgreSQL.
- Displays interactive charts for temperature, precipitation, wind, humidity, and pressure.
- Supports multiple time ranges (12h, 24h, 3 days, 7 days, 30 days, full history).
- Exports filtered data to `downloaded.csv`.

## Tech Stack
- Python (Tkinter desktop UI)
- pandas
- requests + BeautifulSoup
- PostgreSQL (`psycopg2`)
- Plotly

## Requirements
- Python 3.10+
- PostgreSQL
- `uv`

## Setup (uv)
1. Install `uv` and sync environment from `pyproject.toml`:
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv sync
```
2. Create `.env` from the template:
```bash
Copy-Item .env.example .env
```
3. Edit `.env` and set your PostgreSQL credentials.
4. Create a PostgreSQL database (default from template: `html`).

## Database Configuration (.env)
Use these variables in `.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=html
DB_USER=postgres
DB_PASSWORD=your_password
FETCH_INTERVAL_MINUTES=5
```

## Run
```bash
uv run python app.py
```

## Project Files
- `app.py` - Tkinter user interface.
- `functions.py` - scraping, database operations, filtering, plotting, CSV export.
- `data.csv` - latest downloaded source snapshot.
- `downloaded.csv` - user-exported filtered data.
- `.env.example` - environment variables template for local setup.

## Data Source
IMGW public data: `https://danepubliczne.imgw.pl/api/data/synop/format/html`

## License
This project is intended for educational use only.
Licensed under the MIT License. See LICENSE for details.
