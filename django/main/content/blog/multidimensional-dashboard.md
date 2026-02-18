# Multidimensional Data Visualization Dashboard

Interactive dashboard for exploring multidimensional datasets with Plotly and Dash, wrapped in an Eel desktop window.

## Features

- Upload and parse `CSV`, `XLS/XLSX`, `TSV`, and `TXT` files
- Visualize data with Parallel Coordinates and Parallel Categories
- Inspect uploaded data in an interactive Dash table (filter, sort, paginate)
- Run as a desktop app (Eel window) while serving Dash locally

## Tech Stack

- Python 3.11+
- Dash
- Plotly
- Pandas
- Eel
- `uv` for dependency and environment management

## Showcase

### GUI

The application runs as a desktop window (Eel) with an embedded Dash interface. The layout consists of:

- **Tab bar** — two tabs: `Program` (active by default) and `Settings`.
- **File drop zone** — a dashed red-bordered area at the top of the `Program` tab accepting drag-and-drop or manual file selection (`CSV`, `XLSX`, `TSV`, `TXT`).
- **Chart area** — occupies the main body of the window and updates automatically after a file is loaded.
- **Color legend** — a `COLOR_ID` colorbar (dark purple → yellow scale, 0–18) displayed to the right of every chart.

### Visualization Modes

**Parallel Coordinates** (continuous axes) — each data record is drawn as a polyline crossing all numeric axes. Axes shown in the example: `ID`, `KDA`, `VS/min`, `CS/min`, `DMG/min`, `W/L`, `COLOR_ID`. Line color maps to `COLOR_ID`, making clusters and outliers immediately visible against the gradient scale.
<img width="1249" height="806" alt="Parallel Coordinates" src="https://github.com/user-attachments/assets/c8e9d643-e671-4ad2-b1bc-b59d33f60cd4" />

**Parallel Categories** (discrete/binned axes) — records are grouped into colored ribbon bands between axes. The same columns are displayed as stacked categorical segments with labeled tick values. Ribbon width encodes the number of records sharing that value combination, and color again follows the `COLOR_ID` scale, highlighting which category groups dominate each dimension.
<img width="1248" height="790" alt="Parallel Categories" src="https://github.com/user-attachments/assets/8cadcb4a-eca4-470e-94c6-995ef4163b52" />

## Project Structure

```text
.
|- app/
|  |- controller.py
|  |- model.py
|  |- view.py
|  |- data.py
|  |- resourceController.py
|  |- dashApp.py
|  |- assets/
|  \- web/
|     \- main.html
|- Exemplary_data/
|  \- League_of_legends_stats.csv
|- main.py
|- pyproject.toml
\- uv.lock
```

## Getting Started

1. Install dependencies and run app:

```bash
uv sync
uv run python main.py
```

## Runtime Behavior

- Dash server runs at `http://127.0.0.1:8050`.
- Eel starts a local desktop host (default `localhost:8000`, with automatic fallback if the port is busy).
- Closing the desktop window also shuts down the Dash server.

## License

MIT (see `LICENSE`).
