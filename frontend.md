activity-tracker:
# Activity Tracker

A Django web application for tracking physical activity, sharing posts, and generating activity statistics.

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

## Prerequisites

- Python 3.10
- PostgreSQL server running locally
- uv installed (`pip install uv`)

## Quick Start (uv)

1. Clone the repository:

2. Create PostgreSQL database (name must match `DB_NAME` in `.env`):
```sql
CREATE DATABASE activityDB;
```

3. Create `.env` with your local PostgreSQL credentials.
Look at `.env.example`

4. Install dependencies:
```bash
uv sync
```

5. Run migrations and run server
```bash
uv run python manage.py migrate
uv run python manage.py runserver
```

## Database Behavior

The application validates PostgreSQL connection at startup in local mode.
If the database is missing or credentials are invalid, startup fails with `django.db.utils.OperationalError`.

## Tests

```bash
uv run python manage.py test
```

## License

MIT License. See `LICENSE`.
This project is for educational purposes. It was built to practice Django web development, PostgreSQL integration, authentication flows, and basic product design patterns.
analiza-makro-konkurs:
# Tax Burden Distribution Analysis - Competition Project

## Project Overview

This project was prepared for an analytical competition.
The analysis focuses on the distribution of tax burdens in the fictional country **Fiskalia**, based on micro-level tax data.

The main goal is to examine how different income sources and tax regimes affect redistribution outcomes.

## Scope of Analysis

- Government revenue calculations for three tax types: progressive PIT, flat PIT, and capital gains tax.
- Redistribution analysis using empirical/theoretical tax wedge charts, effective tax rates by income decile, and progressivity assessment.
- Two reform scenarios (rate change and allowance plus threshold change), including effects on budget revenue and social groups.

## Tech Stack

- Language: `R`
- Libraries: `dplyr`, `ggplot2`, `gridExtra`, `kableExtra`, `bookdown`
- Report format: `RMarkdown -> PDF`

## Project Structure

```text
data.csv                                      # Input dataset
analiza.Rmd                                   # Main analysis report (RMarkdown)
analiza.pdf                                   # Rendered PDF report
bibliografia.bib                              # Bibliography
Załącznik_nr_2...                             # Competition task statement
```

## How to Run

From RStudio or the R console:

```r
rmarkdown::render("analiza.Rmd")
```

## License

This project is licensed under the MIT License. See `LICENSE` for details.

## Note

This is an educational project. Data and scenarios are fictional.
currency-price-prediction:
# Crypto Currency Price Prediction

Desktop application for cryptocurrency price forecasting with recurrent neural networks (LSTM, GRU, and LSTM+GRU).

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

## Data Modes

- Online mode: `Yahoo` is used for crypto downloads. Selecting `Stooq` or `Naver` shows an "unsupported" warning and auto-switches back to `Yahoo`.
- Offline mode: disable online switch and choose a CSV file.
  Required column: `Close`.
  Recommended column for proper timeline: `Date`.

## License

This project is licensed under the MIT License. See `LICENSE`.

## Notes

- If a data source returns empty data, the app shows a user-facing error dialog.
- This project is educational and should not be treated as trading advice.

granular-data-grouping:
# Granularne grupowanie danych w Pythonie

## Wstęp

Grupowanie danych (ang. clustering) jest jedną z fundamentalnych technik eksploracji danych, stosowaną w wielu dziedzinach nauki i przemysłu, takich jak:

- Analiza biochemiczna (grupowanie sekwencji genów)
- Segmentacja klientów w marketingu
- Wykrywanie anomalii w cyberbezpieczeństwie
- Wizualizacja dużych zbiorów danych

W niniejszym projekcie skupiamy się na **granularnym grupowaniu danych w jedną grupę**. Celem jest wyodrębnienie dużego, wewnętrznie spójnego klastra oraz sklasyfikowanie pozostałych punktów jako szum.

## Dziedzina problemu

1. **Analiza skupień (Cluster Analysis)**
   - Techniki nienadzorowanej klasyfikacji danych bez etykiet.
2. **Obliczenia ziarniste (Granular Computing)**
   - Zarządzanie informacją przez tworzenie granulek danych o różnym poziomie szczegółowości.
3. **Detekcja skupień w szumie**
   - Identyfikacja istotnych struktur nawet w obecności dużej liczby punktów zakłócających.

## Cel badania

- Zaprojektowanie i implementacja metod granularnego grupowania, umożliwiających selekcję **jednego dominującego klastra**.
- Opracowanie ilościowych kryteriów oceny granic klastra.
- Porównanie trzech podejść klasteryzacyjnych: DBSCAN, Single Linkage, Complete Linkage.
- Przeprowadzenie eksperymentów na syntetycznych zbiorach o różnych kształtach i poziomach szumu.
- Ocena wydajności obliczeniowej wszystkich algorytmów.

## Dlaczego jedna grupa?

Typowe algorytmy klasteryzacji dzielą dane na wiele klastrów. W naszym podejściu interesuje nas **jedynie** identyfikacja jednego głównego klastra:

- Koncentracja na najistotniejszej strukturze w danych.
- Uniknięcie nadmiernej segmentacji prowadzącej do artefaktów.
- Jednoznaczne kryteria definiujące granice klastra.

## Zasada uzasadnionej granulacji

Granularne grupowanie opiera się na łączeniu dwóch komplementarnych miar:

1. **Wielkość klastra (N)**
2. **Jednorodność wewnętrzna**:
   - Średnia odległość między punktami (d̄)
   - Średnia odległość do k-tego sąsiada (d_k)

Formuły kryteriów:
```math
P1 = N \times \frac{1}{\bar{d}}                \\
P2 = N \times \left(\frac{1}{\bar{d}}\right)^2  \\
P3 = \sqrt{N} \times \left(\frac{1}{\bar{d}}\right)^2
```
oraz warianty:
```math
P1_k = N \times \frac{1}{d_k},
P2_k = N \times \left(\frac{1}{d_k}\right)^2,
P3_k = \sqrt{N} \times \left(\frac{1}{d_k}\right)^2.
```

## Teoretyczne podstawy algorytmów

### DBSCAN
- Złożoność: \(O(n \log n)\) przy zastosowaniu indeksów przestrzennych; w przeciwnym wypadku \(O(n^2)\).
- Dwa parametry kluczowe: promień ε i minimalna liczba punktów MinPts.

### Single Linkage
- Zasada: odległość między klastrami = minimalna odległość między punktami.
- Zaburzenia: może łączyć długie łańcuchy.

### Complete Linkage
- Zasada: odległość między klastrami = maksymalna odległość między punktami.
- Zaleta: tworzy bardziej zwarte klastry; wada: wrażliwy na izolowane punkty.

## Struktura projektu

```text
project_root/
├── point_generators.py      # Generowanie danych
├── DBscan.py                # Implementacja DBSCAN
├── KNN.py                   # Implementacja algorytmu kNN
├── main.py                  # Skrypt eksperymentalny
├── wyniki_czasu_wykonania.csv
├── requirements.txt
└── results/
    ├── circle/...
    ├── ring/...
    └── normal/...
```

## Wymagania
- Python 3.9+
- Biblioteki:
  - `numpy` (obliczenia numeryczne)
  - `matplotlib` (wizualizacja)
  - `scikit-learn` (implementacja DBSCAN i KNN)
  - `pandas` (przetwarzanie danych)
  - `scipy` (obliczenia hierarchiczne)

## Instalacja

```bash
git clone https://github.com/użytkownik/projekt-klastrowania.git
cd projekt-klastrowania
pip install -r requirements.txt
```

## Użytkowanie przykładowe

### Generowanie danych
```python
import point_generators as pg
# generuj 800 punktów w kole o promieniu 50 + 200 punktów szumu
pg.generate_points_circle(
    output_folder='results/circle',
    noise_points=200,
    circle_radius=50,
    num_points=800,
    max_size=100
)
```

### DBSCAN
```python
from DBscan import DBscanAlgorithmLoop, DBscanChart, DBscan
# iteracja po eps ∈ [2,20], step=0.5, MinPts ∈ [5,50]
DBscanAlgorithmLoop(2,20,0.5,5,50,'results/circle')
# analiza wykresów i wybór optymalnych parametrów
eps, min_pts, p_val = DBscanChart('results/circle', show_picture=True, p_id='p1')
# wykonanie docelowe
DBscan(
    file_path='results/circle/points.txt',
    folder='results/circle',
    epsilon=eps,
    samples=min_pts,
    p_id='p1',
    p_val=p_val
)
```

### Single / Complete Linkage
```python
from main import makeDendrogram, LinkageAlgorithmLoop, LinkageAlgorithm
# oblicz zakres d_min, d_max
d_min, d_max = makeDendrogram('results/circle/points.txt', method='single', draw=True)
# iteracja po 200 krokach
LinkageAlgorithmLoop(
    path='results/circle',
    file_path='results/circle/points.txt',
    method='single',
    max_d=d_min,
    max_d_range=d_max,
    num_measurements=200,
    result_path='results/circle/single/results_loop.csv'
)
# końcowe uruchomienie dla optymalnego d_max
opt_d = 10.5  # wynik z wykresu
LinkageAlgorithm(
    file_path='results/circle/points.txt',
    method='single',
    max_d=opt_d,
    name='opt',
    folder='results/circle',
    show_picture=True
)
```

## Szczegóły implementacji

1. `point_generators.py`:
   - Funkcja `generate_points`: wrapper wybierający odpowiedni generator.
   - Formaty wyjściowe: `points.txt` z trzema kolumnami (x, y, etykieta).

2. `DBscan.py`:
   - `DBscanAlgorithmLoop`: zapisuje wyniki P1–P15 do CSV.
   - `DBscanChart`: rysuje wykresy miar vs eps / MinPts.
   - `DBscan`: generuje ostateczne klastry i zapisuje `DBscanResults.csv`.

3. `KNN.py`:
   - Łatwa integracja z `LinkageAlgorithmLoop` do obliczania metryk P1–P15.

4. `main.py`:
   - Import wszystkich modułów.
   - Konfiguracja parametrów eksperymentu.
   - Pętle po poziomach szumu, promieniach i kształtach.
   - Zapis wyników do `wyniki_czasu_wykonania.csv`.

## Wyniki eksperymentów

| Algorytm        | Dokładność (średnia) | Czas relatywny | Uwagi                             |
|-----------------|----------------------|----------------|-----------------------------------|
| DBSCAN          | 0.89                 | 1.0            | Wrażliwy na ε, MinPts             |
| Single Linkage  | 0.82                 | 0.2            | Dobre dla kształtów łancuchowych  |
| Complete Linkage| 0.75                 | 0.25           | Najgorsze przy dużym szumie       |

## Wnioski

- **Najlepszy** algorytm do granularnego wykrywania jednego klastra: DBSCAN, ale wymaga optymalizacji parametrów.
- **Single Linkage** sprawdza się lepiej przy nietypowych kształtach (von Mises).
- **Complete Linkage** nie polecany w obecności silnego szumu.
- Wzrost udziału szumu powyżej 60% znacząco obniża jakość wszystkich algorytmów.

## Możliwości rozwoju

- Automatyczny dobór parametrów przy użyciu technik optymalizacji globalnej lub uczących się heurystyk.
- Zastosowanie algorytmów hybrydowych (DBSCAN + hierarchiczne).
- Ekstrapolacja na dane wielowymiarowe i dynamiczne strumienie danych.

## Autor i licencja

- **Autor**: Krystian Stasica
- **Licencja**: MIT

---

# Granular Data Clustering in Python

## Introduction

Data clustering is one of the fundamental techniques of data exploration, used in many fields of science and industry, such as:

- Biochemical analysis (clustering of gene sequences)
- Customer segmentation in marketing
- Anomaly detection in cybersecurity
- Visualization of large datasets

In this project, we focus on **granular data clustering into a single group**. The goal is to extract a large, internally coherent cluster and classify the remaining points as noise.

## Problem Domain

1. **Cluster Analysis**
   - Techniques of unsupervised classification of unlabeled data.
2. **Granular Computing**
   - Information management by creating data granules at different levels of detail.
3. **Cluster Detection in Noise**
   - Identification of significant structures even in the presence of a large number of interfering points.

## Research Objectives

- Design and implementation of granular clustering methods, enabling the selection of **one dominant cluster**.
- Development of quantitative criteria for evaluating cluster boundaries.
- Comparison of three clustering approaches: DBSCAN, Single Linkage, Complete Linkage.
- Conducting experiments on synthetic datasets with different shapes and noise levels.
- Evaluation of computational efficiency of all algorithms.

## Why One Group?

Typical clustering algorithms divide data into multiple clusters. In our approach, we are **only** interested in identifying one main cluster:

- Focus on the most significant structure in the data.
- Avoiding excessive segmentation leading to artifacts.
- Unambiguous criteria defining cluster boundaries.

## Principle of Justified Granulation

Granular clustering is based on combining two complementary measures:

1. **Cluster Size (N)**
2. **Internal Homogeneity**:
   - Average distance between points (d̄)
   - Average distance to the k-th neighbor (d_k)

Criteria formulas:
```math
P1 = N \times \frac{1}{\bar{d}}                \\
P2 = N \times \left(\frac{1}{\bar{d}}\right)^2  \\
P3 = \sqrt{N} \times \left(\frac{1}{\bar{d}}\right)^2
```
and variants:
```math
P1_k = N \times \frac{1}{d_k},
P2_k = N \times \left(\frac{1}{d_k}\right)^2,
P3_k = \sqrt{N} \times \left(\frac{1}{d_k}\right)^2.
```

## Theoretical Foundations of Algorithms

### DBSCAN
- Complexity: \(O(n \log n)\) when using spatial indexes; otherwise \(O(n^2)\).
- Two key parameters: radius ε and minimum number of points MinPts.

### Single Linkage
- Principle: distance between clusters = minimum distance between points.
- Disturbances: may connect long chains.

### Complete Linkage
- Principle: distance between clusters = maximum distance between points.
- Advantage: creates more compact clusters; disadvantage: sensitive to isolated points.

## Project Structure

```text
project_root/
├── point_generators.py      # Data generation
├── DBscan.py                # DBSCAN implementation
├── KNN.py                   # kNN algorithm implementation
├── main.py                  # Experimental script
├── wyniki_czasu_wykonania.csv
├── requirements.txt
└── results/
    ├── circle/...
    ├── ring/...
    └── normal/...
```

## Requirements
- Python 3.9+
- Libraries:
  - `numpy` (numerical calculations)
  - `matplotlib` (visualization)
  - `scikit-learn` (DBSCAN and KNN implementation)
  - `pandas` (data processing)
  - `scipy` (hierarchical calculations)

## Installation

```bash
git clone https://github.com/user/clustering-project.git
cd clustering-project
pip install -r requirements.txt
```

## Example Usage

### Data Generation
```python
import point_generators as pg
# generate 800 points in a circle with radius 50 + 200 noise points
pg.generate_points_circle(
    output_folder='results/circle',
    noise_points=200,
    circle_radius=50,
    num_points=800,
    max_size=100
)
```

### DBSCAN
```python
from DBscan import DBscanAlgorithmLoop, DBscanChart, DBscan
# iterate over eps ∈ [2,20], step=0.5, MinPts ∈ [5,50]
DBscanAlgorithmLoop(2,20,0.5,5,50,'results/circle')
# analyze charts and select optimal parameters
eps, min_pts, p_val = DBscanChart('results/circle', show_picture=True, p_id='p1')
# final execution
DBscan(
    file_path='results/circle/points.txt',
    folder='results/circle',
    epsilon=eps,
    samples=min_pts,
    p_id='p1',
    p_val=p_val
)
```

### Single / Complete Linkage
```python
from main import makeDendrogram, LinkageAlgorithmLoop, LinkageAlgorithm
# calculate d_min, d_max range
d_min, d_max = makeDendrogram('results/circle/points.txt', method='single', draw=True)
# iterate over 200 steps
LinkageAlgorithmLoop(
    path='results/circle',
    file_path='results/circle/points.txt',
    method='single',
    max_d=d_min,
    max_d_range=d_max,
    num_measurements=200,
    result_path='results/circle/single/results_loop.csv'
)
# final run for optimal d_max
opt_d = 10.5  # result from chart
LinkageAlgorithm(
    file_path='results/circle/points.txt',
    method='single',
    max_d=opt_d,
    name='opt',
    folder='results/circle',
    show_picture=True
)
```

## Implementation Details

1. `point_generators.py`:
   - Function `generate_points`: wrapper selecting the appropriate generator.
   - Output formats: `points.txt` with three columns (x, y, label).

2. `DBscan.py`:
   - `DBscanAlgorithmLoop`: saves P1–P15 results to CSV.
   - `DBscanChart`: draws charts of measures vs eps / MinPts.
   - `DBscan`: generates final clusters and saves `DBscanResults.csv`.

3. `KNN.py`:
   - Easy integration with `LinkageAlgorithmLoop` for calculating P1–P15 metrics.

4. `main.py`:
   - Import of all modules.
   - Configuration of experiment parameters.
   - Loops over noise levels, radii, and shapes.
   - Saving results to `wyniki_czasu_wykonania.csv`.

## Experimental Results

| Algorithm       | Accuracy (average) | Relative Time | Notes                             |
|-----------------|-------------------|--------------|-----------------------------------|
| DBSCAN          | 0.89              | 1.0          | Sensitive to ε, MinPts            |
| Single Linkage  | 0.82              | 0.2          | Good for chain-like shapes        |
| Complete Linkage| 0.75              | 0.25         | Worst with high noise             |

## Conclusions

- **Best** algorithm for granular detection of a single cluster: DBSCAN, but requires parameter optimization.
- **Single Linkage** performs better with atypical shapes (von Mises).
- **Complete Linkage** not recommended in the presence of strong noise.
- Increase in noise share above 60% significantly reduces the quality of all algorithms.

## Development Possibilities

- Automatic parameter selection using global optimization techniques or learning heuristics.
- Application of hybrid algorithms (DBSCAN + hierarchical).
- Extrapolation to multidimensional data and dynamic data streams.

## Author and License

- **Author**: Krystian Stasica
- **License**: MIT
multidimensional-dashboard:
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
my-django-portfolio:
# Django Portfolio Blog

This repository contains a Django portfolio/blog project using PostgreSQL.

## Running with Docker

### Prerequisites
- Docker
- Docker Compose

### Quick Start
```bash
# Rename .env.example to .env
cp .env.example .env

# Start all services in detached mode
docker-compose up --build -d
```

This will:
- Start PostgreSQL
- Build and run Django with Gunicorn
- Serve static files through Caddy
- Run `web` from the image filesystem (no source bind mount to `/app`)

Open `https://localhost`.

To stop:
```bash
docker-compose down
```

## Local Setup

### Prerequisites
- Python 3.x
- PostgreSQL
- [uv](https://github.com/astral-sh/uv)

### 1. Clone
```bash
git clone https://github.com/stokuj/my_django_portfolio.git
cd my_django_portfolio
```

### 2. Configure env
```bash
cp .env.example .env
```

Generate a secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Create database
```sql
psql -U postgres
CREATE DATABASE your_db_name;
\q
```

### 4. Install and run
```bash
uv sync

# Generate Tailwind CSS
npm install
npm run build:css

# Run Django
python django/manage.py migrate
python django/manage.py collectstatic --noinput
python django/manage.py runserver
```
Open `http://localhost:8000`.

## Project Structure
```text
MY-DJANGO-PORTFOLIO/
|-- .github/
|-- django/
|   |-- entrypoints/
|   |-- main/
|   |-- personal_portfolio/
|   `-- manage.py
|-- media/
|-- staticfiles/
|-- Caddyfile
|-- docker-compose.yml
|-- Dockerfile
|-- LICENSE
|-- Makefile
|-- package-lock.json
|-- package.json
|-- pyproject.toml
|-- README.md
|-- tailwind.config.js
`-- uv.lock
```

## Technologies

- Python 3.13
- Django 5.1.7
- PostgreSQL
- Tailwind CSS + DaisyUI
- Gunicorn
- Docker + Docker Compose

## Features

- Project detail pages
- Status and tag system
- Project filtering
- PostgreSQL-backed data model
- Visitor counter
- Responsive UI
- Media file handling

## Solved Problems

- Problem: startup `.sh` script failed because of CRLF line endings.
  Solution: convert script line endings to LF.

- Problem: Caddy failed with `server block without any key...`.
  Solution: set `APP_DOMAIN` in `.env` (for example `APP_DOMAIN=localhost`).

- Problem: missing static files after deploy.
  Solution: run `docker-compose exec web python manage.py collectstatic`.

- Problem: `style.css` stopped updating after project reorganization.
  Solution: run `npm run build:css` and use path `./django/main/static/src/css/input.css -> ./django/main/static/css/style.css`.

## Additional Developer Information

### Static Files
- Run `python django/manage.py collectstatic` for production static files.

### Frontend
1. Tailwind config is in `tailwind.config.js`.
2. Place static files in `django/main/static/`.

### Deployment
1. Gunicorn is used as the WSGI server.

## Author

- Name: Krystian Stasica
- Portfolio: TODO
- LinkedIn: TODO
- Email: TODO

## License

This project is available under the MIT License. See [LICENSE](LICENSE).
NTwI-obliczenia-ziarniste:
# Obliczenia na Liczbach Rozmytych (Fuzzy Numbers)

Projekt "odleglosc rozmyta granul" z przedmiotu Nowe Technologie w Informatyce.

## Opis projektu

Program implementuje operacje na liczbach rozmytych (fuzzy numbers), reprezentowanych jako trojkatne funkcje przynaleznosci.

W projekcie liczba rozmyta jest reprezentowana przez trzy parametry:
- **x1** (lewy punkt) - dolna granica nosnika funkcji przynaleznosci
- **m** (srodek) - wartosc z maksymalna przynaleznoscia (rowna 1)
- **x2** (prawy punkt) - gorna granica nosnika funkcji przynaleznosci

Program umozliwia wykonywanie operacji:
- wyswietlanie pojedynczej liczby rozmytej,
- mnozenie liczby rozmytej przez liczbe rzeczywista,
- potegowanie liczby rozmytej,
- dodawanie dwoch liczb rozmytych,
- odejmowanie dwoch liczb rozmytych,
- mnozenie dwoch liczb rozmytych.

## Wymagania

- Python 3.10+
- uv

## Instalacja & Uzycie

Zainstaluj zaleznosci:
```bash
uv sync
```

### Wyswietlanie pojedynczej liczby rozmytej

```bash
uv run python app.py x1 m x2
```

Przyklad:
```bash
uv run python app.py 2 3 4
```

### Mnozenie przez liczbe rzeczywista lub potegowanie

```bash
uv run python app.py x1 m x2 operator liczba
```

Przyklady:
```bash
uv run python app.py 2 3 4 * 2
uv run python app.py 2 3 4 ^ 2
```

### Operacje na dwoch liczbach rozmytych

```bash
uv run python app.py x1_A m_A x2_A operator x1_B m_B x2_B
```

Przyklady:
```bash
uv run python app.py 2 3 4 + 5 6 7
uv run python app.py 2 3 4 - 1 2 3
uv run python app.py 2 3 4 * 1 2 3
```

### Lancuch operacji na wielu liczbach rozmytych

```bash
uv run python app.py x1_A m_A x2_A operator1 x1_B m_B x2_B operator2 x1_C m_C x2_C ...
```

Przyklad:
```bash
uv run python app.py 2 3 4 + 5 6 7 - 1 2 3
```

## Teoria zbiorow rozmytych

Zbior rozmyty to zbior, w ktorym kazdy element nalezy do zbioru z pewnym stopniem przynaleznosci z przedzialu [0, 1].
W projekcie uzyta jest trojkatna funkcja przynaleznosci okreslona przez parametry `x1`, `m`, `x2`.

## Autor

Krystian Stasica

## Licencja

Projekt jest udostepniony na licencji MIT. Zobacz plik `LICENSE`.
weather-web-scraping:
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
web-scraping-lubimyczytac:
# Lubimyczytac Scraper to Goodreads Pipeline

A Selenium-based data pipeline that reads a public Lubimyczytac profile library, enriches book records with per-book metadata, and exports a Goodreads-compatible CSV.

## Scope

- Source: public Lubimyczytac profile library pages
- Output: normalized local CSV files, including Goodreads import format

## Stack

- Python 3
- Selenium + ChromeDriver
- uv (environment and dependency management)

## Project Layout

```text
.
|-- scraper/
|   |-- profile_scraper.py   # phase 1: list scraping from profile pages
|   |-- enrichment.py        # phase 2: per-book enrichment orchestration
|   |-- book_details.py      # phase 2: ISBN/original title extraction
|   `-- __init__.py
|-- models/
|   |-- book.py              # Book dataclass and CSV schema
|   `-- __init__.py
|-- data_io/
|   |-- csv_utils.py         # CSV read/write and Goodreads export mapping
|   `-- __init__.py
|-- dane/
|   |-- books.csv            # phase 1 output
|   |-- books_enriched.csv   # phase 2 output
|   `-- goodreads.csv        # phase 3 output
|-- tests/
|-- main.py                  # pipeline entry point
|-- config.example.ini
|-- pyproject.toml
`-- LICENSE
```

## Setup (uv)

1. Install `uv` (if missing):

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. Sync dependencies:

```bash
uv sync
```

3. Ensure Google Chrome and a compatible ChromeDriver are available in `PATH`.

## Configuration & Running

Create your local config.ini from the config.example.ini:


Then edit `config.ini`:

```ini
[settings]
profile_url = https://lubimyczytac.pl/profil/YOUR_PROFILE_ID/YOUR_PROFILE_NAME
```

Run the pipeline entry point:

```bash
uv run python main.py
```

## Phase Artifacts Summary

- `dane/books.csv`: raw list scrape from profile pages (phase 1)
- `dane/books_enriched.csv`: per-book ISBN and original title enrichment (phase 2)
- `dane/goodreads.csv`: Goodreads import-ready export (phase 3)
## Pipeline Phases

### Phase 1: Profile Scraping

- Module: `scraper/profile_scraper.py`
- Entry function: `scrape_books(profile_url)`
- Input:
  - `profile_url` from `config.ini` (expanded in `main.py` with list query parameters)
- Processing:
  - Opens profile library pages in Selenium
  - Iterates pagination
  - Extracts row-level metadata (title, author, ratings, shelves, link, etc.)
  - Produces `Book` objects (domain model) before CSV serialization
- Output file:
  - `dane/books.csv` via `save_books_to_csv(...)`
- Shelf fields in this phase:
  - `Na półkach Główne`: primary state shelf (e.g. `Przeczytane`, `Teraz czytam`, `Chcę przeczytać`)
  - `Na półkach Pozostałe`: custom user shelves/tags (optional)

### Phase 2: Record Enrichment

- Modules: `scraper/enrichment.py`, `scraper/book_details.py`
- Entry function: `fill_isbn_and_original_titles(books)`
- Input file:
  - `dane/books.csv` loaded by `load_books_from_csv(...)`
- Processing:
  - Visits each book URL from column `Link`
  - Extracts ISBN and original title from the book detail page
  - Fills missing original title fallback with the Polish title
- Output file:
  - `dane/books_enriched.csv` via `save_books_to_csv(...)`

### Phase 3: Goodreads Conversion

- Module: `data_io/csv_utils.py`
- Entry function: `convert_books_to_goodreads(input_file, output_file)`
- Input file:
  - `dane/books_enriched.csv`
- Processing:
  - Maps Lubimyczytac columns to Goodreads import schema
  - `Na półkach Główne` -> Goodreads `Shelves`
  - `Na półkach Pozostałe` -> Goodreads `Bookshelves`
  - Writes Goodreads-required headers and transformed rows
- Output file:
  - `dane/goodreads.csv`

## Educational Purpose

This project is intended for educational use only. It is designed to demonstrate web scraping workflow design, CSV data processing, and multi-phase data transformation in Python.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
