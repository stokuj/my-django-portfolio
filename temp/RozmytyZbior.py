import numpy as np
import matplotlib.pyplot as plt

class RozmytyZbior:
    """
    Klasa reprezentująca zbiór rozmyty.

    Atrybuty:
        x1 (float): Lewy koniec przedziału, na którym działa funkcja przynależności.
        x2 (float): Prawy koniec przedziału, na którym działa funkcja przynależności.
        m (float): Parametr określający rozmycie funkcji przynależności.
        x (float): tablica punktów, dla któreych obliczamy wartość funkcji przynależności.
        funkcja_przynaleznosci(): reprezentuje wartość funkcji przynależności dla punktu x.

    Metody:
        __init__(self, x1, m, x2, x):
            Inicjalizuje obiekt zbioru rozmytego.

        dodaj(self, inny_zbior):
            Dodaje dwa zbiory rozmyte.

        odejmij(self, inny_zbior):
            Odejmuje dwa zbiory rozmyte.

        pomnóż(self, liczba):
            Mnoży zbiór rozmyty przez liczbę.

        potęgowanie(self, liczba):
            Podnosi zbiór rozmyty do potęgi.

        wyswietl(self, subplot):
            Wyświetla zbiór rozmyty na wykresie.

    """
    def __init__(self, x1, m, x2, x):
        """
        Inicjalizuje obiekt zbiór rozmytego.

        :param x1: Lewy koniec przedziału, na którym działa funkcja przynależności.
        :param m: Parametr określający rozmycie funkcji przynależności.
        :param x2: Prawy koniec przedziału, na którym działa funkcja przynależności.
        :param x: Tablica punktów, dla których obliczamy wartość funkcji przynależności.
        """
        self.x1 = x1
        self.x2 = x2
        self.m = m
        self.x = x
        self.funkcja_przynaleznosci = np.where((x >= x1) & (x <= m), (x - x1) / (m - x1), np.where((x > m) & (x <= x2), (x2 - x) / (x2 - m), 0))

    def dodaj(self, inny_zbior):
        """
        Dodaje dwa zbiory rozmyte.

        :param inny_zbior: Inny zbiór rozmyty do dodania.
        :return: Nowy zbiór rozmyty będący wynikiem dodawania.
        """
        m = self.m + inny_zbior.m
        x1=(m-abs(self.m-self.x1)+(m-abs(inny_zbior.m-inny_zbior.x1)))/2
        x2=(m+abs(self.m-self.x2)+(m+abs(inny_zbior.m-inny_zbior.x2)))/2
        return RozmytyZbior(x1, m, x2, np.arange(x1-0.2, x2+0.2, 0.01))

    def odejmij(self, inny_zbior):
        """
        Odejmuje dwa zbiory rozmyte.

        :param inny_zbior: Inny zbiór rozmyty do odjęcia.
        :return: Nowy zbiór rozmyty będący wynikiem odejmowania.
        """
        m = self.m - inny_zbior.m
        x1=(m-abs(self.m-self.x1)+(m-abs(inny_zbior.m-inny_zbior.x1)))/2
        x2=(m+abs(self.m-self.x2)+(m+abs(inny_zbior.m-inny_zbior.x2)))/2
        return RozmytyZbior(x1, m, x2, np.arange(x1-0.2, x2+0.2, 0.01))

    def pomnóż(self, liczba):
        """
        Mnoży zbiór rozmyty przez liczbę.

        :param liczba: Liczba, przez którą mnożymy zbiór rozmyty.
        :return: Nowy zbiór rozmyty będący wynikiem mnożenia.
        """
        m = self.m * liczba
        x1=(m-abs(self.m-self.x1))
        x2=(m+abs(self.m-self.x2))
        return RozmytyZbior(x1, m, x2, np.arange(x1-0.2, x2+0.2, 0.01))

    def potęgowanie(self, liczba):
        """
        Podnosi zbiór rozmyty do potęgi.

        :param liczba: Potęga, do której podnosimy zbiór rozmyty.
        :return: Nowy zbiór rozmyty będący wynikiem potęgowania.
        """
        m = self.m ** liczba
        x1=(m-abs(self.m-self.x1))
        x2=(m+abs(self.m-self.x2))
        return RozmytyZbior(x1, m, x2, np.arange(x1-0.2, x2+0.2, 0.01))

    def wyswietl(self, subplot):
        """
        Wyświetla figure

        :param subplot: Figura, która będzie prezentowana.
        """
        plt.subplot(subplot)
        plt.plot(self.x, self.funkcja_przynaleznosci, linewidth=1.5)

    ### Inne warianty

    def pomnoz_przez_zbior(self, inny_zbior):
        """
        Mnoży dwa zbiory rozmyte (pierwszy wariant).

        Ta metoda implementuje mnożenie dwóch zbiorów rozmytych, gdzie nowy środek
        jest iloczynem środków, a nowe punkty brzegowe są obliczane jako średnia
        z odpowiednich odległości od środka.

        :param inny_zbior: Inny zbiór rozmyty do pomnożenia.
        :return: Nowy zbiór rozmyty będący wynikiem mnożenia.
        """
        m = self.m * inny_zbior.m
        x1=(m-abs(self.m-self.x1)+(m-abs(inny_zbior.m-inny_zbior.x1)))/2
        x2=(m+abs(self.m-self.x2)+(m+abs(inny_zbior.m-inny_zbior.x2)))/2
        return RozmytyZbior(x1, m, x2,  np.arange(x1-0.2, x2+0.2, 0.01))

    def pomnoz_przez_zbior2(self, inny_zbior):
        """
        Mnoży dwa zbiory rozmyte (drugi wariant).

        Ta metoda implementuje alternatywny sposób mnożenia dwóch zbiorów rozmytych,
        gdzie nowy środek jest iloczynem środków, a nowe punkty brzegowe są obliczane
        na podstawie maksymalnych odległości od środka.

        :param inny_zbior: Inny zbiór rozmyty do pomnożenia.
        :return: Nowy zbiór rozmyty będący wynikiem mnożenia.
        """
        m = self.m * inny_zbior.m
        x1 = m - max((self.m-self.x1)*inny_zbior.m,(inny_zbior.m-inny_zbior.x1)*self.m)
        x2 = m + max((self.x2-self.m)*inny_zbior.m,(inny_zbior.x2-inny_zbior.m)*self.m)
        return RozmytyZbior(x1, m, x2,  np.arange(x1-0.2, x2+0.2, 0.01))
