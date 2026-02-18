# Crypto Currency Price Prediction

Desktop application for cryptocurrency price forecasting with recurrent neural networks (LSTM, GRU, and LSTM+GRU).
This project is educational and should not be treated as trading advice.
## Overview

The project uses a Tkinter GUI (MVC structure) to:
- select a market (`BTC`, `ETH`, `DOGE`, `LTC`),
- choose a model architecture,
- train on online or local CSV data,
- visualize predicted vs. actual prices,
- calculate simple gain over a selected window.

Training runs in a background thread. Progress and ETA are shown in:
- terminal logs,
- GUI status line.

## Tech Stack

- Python `>=3.10,<3.13`
- TensorFlow / Keras
- NumPy, Pandas, scikit-learn
- Matplotlib
- yfinance + pandas-datareader
- Tkinter (Azure theme)
- uv (dependency and environment management)

## Project Structure

```text
.
|-- app.py                 # Application entry point (Controller)
|-- app/
|   |-- model.py           # Data access, training, prediction, gain
|   |-- view.py            # Tkinter GUI
|   |-- azure.tcl          # GUI theme
|   |-- test.csv           # Default local CSV for offline mode
|   |-- assets/
|   `-- images/
|-- DATA/
|   `-- download.py        # Utility script for fetching CSV data
|-- DOC/                   # Report and presentation materials
|-- pyproject.toml
`-- uv.lock
```

## Quick Start

1. Install dependencies and run the app:

```bash
uv sync
uv run python app.py
```

## Using the App

1. Choose currency, data source, and model type.
2. Configure `Prediction days`, `Future days`, and `Plot range`.
3. Click `Train`.
4. Monitor progress in terminal and GUI status line.
5. Click `Plot` to show the chart.
6. Click `GAIN` to compute percent change.

## Data and Date Semantics

- `Prediction days`: lookback window size (how many past observations are used as input).
- `Future days`: forecast horizon in days (for example, `1` means predict one day ahead).
- `Plot range`: number of dated points displayed on the chart.
- Chart X-axis now uses concrete calendar dates (`YYYY-MM-DD`).
- Predicted series is shifted by `Future days`, so each predicted point is plotted at its target date.

## Showcase

### GUI

The application features a clean desktop interface built with Tkinter (Azure theme), organized into four panels:

- **Select Currency** — radio buttons to choose between BTC, ETH, Doge, and LTC.
- **Online Source** — selects the data provider: Yahoo, Stooq, or Naver.
- **Select Model** — picks the neural network architecture: LSTM, GRU, or LSTM+GRU.
- **Settings panel** (top-right) — sliders for `Prediction` lookback and data window (`Based on last 30 days`), a toggle to enable/disable the online database, and spinboxes for `Future days` and `Plot range`.
- **Action buttons** — `Train` starts model training in a background thread, `Plot` renders the forecast chart, `GAIN` computes percent price change, `Select file` loads a local CSV for offline mode, and `HELP` opens documentation.

<img width="506" height="571" alt="GUI_DEMO" src="https://github.com/user-attachments/assets/d0f29ff3-1099-49e8-b2f7-cc3c25a6d892" />

### Prediction Chart

After training, clicking `Plot` opens a Matplotlib chart comparing **Actual Prices** (cyan) against **Predicted Prices** (dark purple) over the selected date range. The predicted series is shifted forward by `Future days`, so each predicted point aligns with its target date. The example below shows a BTC forecast over a 20-day window, where the model closely tracks the sharp price rise from ~84 000 to ~94 000 USD.

<img width="640" height="480" alt="Figure_1" src="https://github.com/user-attachments/assets/7feaf790-c0e9-4dd0-885d-784bcfb7e537" />

## License

This project is licensed under the MIT License. See `LICENSE`.
 

