# Obliczenia na Liczbach Rozmytych (Fuzzy Numbers)

Projekt "odległość rozmyta granul" z przedmiotu Nowe Technologie w Informatyce.

## Opis projektu

Program implementuje operacje na liczbach rozmytych (fuzzy numbers) reprezentowanych jako trójkątne funkcje przynależności. Liczby rozmyte są używane w logice rozmytej i teorii zbiorów rozmytych do reprezentowania nieprecyzyjnych wartości.

W tym projekcie liczba rozmyta jest reprezentowana przez trzy parametry:
- **x1** (lewy punkt) - dolna granica nośnika funkcji przynależności
- **m** (środek) - wartość z maksymalną przynależnością (równą 1)
- **x2** (prawy punkt) - górna granica nośnika funkcji przynależności

Program umożliwia wykonywanie następujących operacji:
- Wyświetlanie pojedynczej liczby rozmytej
- Mnożenie liczby rozmytej przez liczbę rzeczywistą
- Potęgowanie liczby rozmytej
- Dodawanie dwóch liczb rozmytych
- Odejmowanie dwóch liczb rozmytych
- Mnożenie dwóch liczb rozmytych

## Wymagania

- Python 3.x
- NumPy
- Matplotlib

## Instalacja

1. Sklonuj repozytorium:
```
git clone https://github.com/username/NTwI-obliczenia-ziarniste-krystian-stasica.git
cd NTwI-obliczenia-ziarniste-krystian-stasica
```

2. Zainstaluj wymagane biblioteki:
```
pip install numpy matplotlib
```

## Użycie

Program jest uruchamiany z linii poleceń z różnymi argumentami w zależności od operacji, którą chcemy wykonać.

### Wyświetlanie pojedynczej liczby rozmytej

```
python app.py x1 m x2
```

Gdzie:
- `x1` - lewy punkt
- `m` - środek (wartość z maksymalną przynależnością)
- `x2` - prawy punkt

Przykład:
```
python app.py 2 3 4
```

### Mnożenie liczby rozmytej przez liczbę rzeczywistą lub potęgowanie

```
python app.py x1 m x2 operator liczba
```

Gdzie:
- `x1`, `m`, `x2` - parametry liczby rozmytej
- `operator` - "*" dla mnożenia lub "^" dla potęgowania
- `liczba` - liczba rzeczywista do mnożenia lub wykładnik potęgi

Przykłady:
```
python app.py 2 3 4 * 2
python app.py 2 3 4 ^ 2
```

### Operacje na dwóch liczbach rozmytych (dodawanie, odejmowanie, mnożenie)

```
python app.py x1_A m_A x2_A operator x1_B m_B x2_B
```

Gdzie:
- `x1_A`, `m_A`, `x2_A` - parametry pierwszej liczby rozmytej (A)
- `operator` - "+" dla dodawania, "-" dla odejmowania, "*" dla mnożenia
- `x1_B`, `m_B`, `x2_B` - parametry drugiej liczby rozmytej (B)

Przykłady:
```
python app.py 2 3 4 + 5 6 7
python app.py 2 3 4 - 1 2 3
python app.py 2 3 4 * 1 2 3
```

### Łańcuch operacji na wielu liczbach rozmytych

Program obsługuje również łańcuch operacji na wielu liczbach rozmytych:

```
python app.py x1_A m_A x2_A operator1 x1_B m_B x2_B operator2 x1_C m_C x2_C ...
```

Przykład:
```
python app.py 2 3 4 + 5 6 7 - 1 2 3
```

## Teoria zbiorów rozmytych

### Podstawowe pojęcia

Zbiór rozmyty to zbiór, w którym każdy element należy do zbioru z pewnym stopniem przynależności z przedziału [0, 1]. W przeciwieństwie do klasycznej teorii zbiorów, gdzie element albo należy do zbioru (przynależność 1), albo nie należy (przynależność 0), w zbiorach rozmytych element może należeć do zbioru częściowo.

Funkcja przynależności μ(x) określa stopień przynależności elementu x do zbioru rozmytego. W tym projekcie używamy trójkątnej funkcji przynależności, która jest określona przez trzy parametry: x1, m, x2.

### Operacje na zbiorach rozmytych

W projekcie zaimplementowano następujące operacje:

1. **Dodawanie**: Jeśli A i B są liczbami rozmytymi, to A + B jest liczbą rozmytą, której parametry są obliczane jako:
   - m = m_A + m_B
   - x1 i x2 są obliczane na podstawie odległości od środka

2. **Odejmowanie**: Jeśli A i B są liczbami rozmytymi, to A - B jest liczbą rozmytą, której parametry są obliczane jako:
   - m = m_A - m_B
   - x1 i x2 są obliczane na podstawie odległości od środka

3. **Mnożenie przez liczbę rzeczywistą**: Jeśli A jest liczbą rozmytą, a k jest liczbą rzeczywistą, to A * k jest liczbą rozmytą, której parametry są obliczane jako:
   - m = m_A * k
   - x1 i x2 są obliczane na podstawie odległości od środka

4. **Potęgowanie**: Jeśli A jest liczbą rozmytą, a n jest liczbą rzeczywistą, to A^n jest liczbą rozmytą, której parametry są obliczane jako:
   - m = m_A^n
   - x1 i x2 są obliczane na podstawie odległości od środka

5. **Mnożenie dwóch liczb rozmytych**: Jeśli A i B są liczbami rozmytymi, to A * B jest liczbą rozmytą, której parametry są obliczane jako:
   - m = m_A * m_B
   - x1 i x2 są obliczane na podstawie odległości od środka

## Autor

Krystian Stasica
