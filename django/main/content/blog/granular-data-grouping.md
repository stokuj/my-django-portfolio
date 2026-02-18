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
