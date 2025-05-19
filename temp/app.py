import sys
import numpy as np
import matplotlib.pyplot as plt
from RozmytyZbior import RozmytyZbior

# Program do operacji na liczbach rozmytych (fuzzy numbers)
# Autor: Krystian Stasica
# Przedmiot: Nowe Technologie w Informatyce
#
# Program obsługuje następujące operacje:
# - Wyświetlanie pojedynczej liczby rozmytej
# - Mnożenie liczby rozmytej przez liczbę rzeczywistą
# - Potęgowanie liczby rozmytej
# - Dodawanie dwóch liczb rozmytych
# - Odejmowanie dwóch liczb rozmytych
# - Mnożenie dwóch liczb rozmytych

### Przypadek wyświetlania liczby - obsługa 3 argumentów (lp, śr, pp)
if len(sys.argv) == 4:
    try:
        lp = float(sys.argv[1])
        śr = float(sys.argv[2])
        pp = float(sys.argv[3])

        # Sprawdzenie czy mamy poprawny trójkąt (lp <= śr <= pp)
        # lp - lewy punkt, śr - środek (wartość z maksymalną przynależnością), pp - prawy punkt
        if not (lp<=śr<=pp):
            raise ValueError
        # Zapobieganie sytuacji, gdy lewy punkt jest równy środkowi
        if lp==śr:
            lp=lp-0.01
        # Zapobieganie sytuacji, gdy prawy punkt jest równy środkowi
        if pp==śr:
            pp=pp+0.01

        # Tworzenie obiektu liczby rozmytej (trójkątnej)
        # Parametry: lewy punkt, środek, prawy punkt, zakres wartości x do obliczeń
        A = RozmytyZbior(lp,śr,pp,np.arange(lp-0.2, pp+0.2, 0.01))

        # Wyświetlanie liczby rozmytej na wykresie
        plt.figure(figsize=(12, 4))
        A.wyswietl(111)  # Wyświetlenie na pojedynczym wykresie (1 wiersz, 1 kolumna, pozycja 1)
        # Wypisanie parametrów liczby rozmytej: lewy punkt, środek, prawy punkt
        print("A:{:<7} {:<7} {:<7}".format(round(A.x1, 2), round(A.m, 2), round(A.x2, 2)))
        plt.title('A')
        plt.xlabel('Wartość')
        plt.ylabel('Stopień przynależności')
        plt.tight_layout()
        plt.show()

    except ValueError:
        print("Niepoprawne argumenty. ")

### Przypadek mnożenia lub potęgowania - obsługa 5 argumentów (lp, śr, pp, operator, liczba)
elif len(sys.argv) == 6:
    operator = sys.argv[4]  # Operator może być "*" (mnożenie) lub "^" (potęgowanie)
    if operator in ("*", "^"):
        try:
            # Parametry liczby rozmytej A
            lp = float(sys.argv[1])  # lewy punkt
            śr = float(sys.argv[2])  # środek (wartość z maksymalną przynależnością)
            pp = float(sys.argv[3])  # prawy punkt
            liczba = float(sys.argv[5])  # liczba rzeczywista do mnożenia lub wykładnik potęgi

            # Sprawdzenie czy mamy poprawny trójkąt (lp <= śr <= pp)
            if not (lp<=śr<=pp):
                raise ValueError
            # Zapobieganie sytuacji, gdy lewy punkt jest równy środkowi
            if lp==śr:
                lp=lp-0.01
            # Zapobieganie sytuacji, gdy prawy punkt jest równy środkowi
            if pp==śr:
                pp=pp+0.01

            # Tworzenie obiektu liczby rozmytej A
            A = RozmytyZbior(lp,śr,pp,np.arange(lp-0.2, pp+0.2, 0.01))

            # Wykonanie odpowiedniej operacji na liczbie rozmytej
            if operator == "*":
                B = A.pomnóż(liczba)  # Mnożenie liczby rozmytej przez liczbę rzeczywistą
            else:  # operator == "^"
                B = A.potęgowanie(liczba)  # Potęgowanie liczby rozmytej

            # Wyświetlanie liczb rozmytych na wykresach
            plt.figure(figsize=(12, 4))

            # Pierwszy podwykres: liczba rozmyta A
            A.wyswietl(311)  # 3 wiersze, 1 kolumna, pozycja 1
            plt.title('A')

            # Drugi podwykres: wynik operacji (B)
            B.wyswietl(312)  # 3 wiersze, 1 kolumna, pozycja 2
            if operator == "*":
                plt.title('A*{}'.format(liczba))
            else:
                plt.title('A^{}'.format(liczba))

            # Trzeci podwykres: porównanie A i wyniku operacji
            A.wyswietl(313)  # 3 wiersze, 1 kolumna, pozycja 3
            B.wyswietl(313)
            if operator == "*":
                plt.title('A i A*{}'.format(liczba))
            else:
                plt.title('A i A^{}'.format(liczba))

            # Wypisanie parametrów liczb rozmytych: lewy punkt, środek, prawy punkt
            print("A:{:<7} {:<7} {:<7} B:{:<7} {:<7} {:<7}".format(
                round(A.x1, 2), round(A.m, 2), round(A.x2, 2), 
                round(B.x1, 2), round(B.m, 2), round(B.x2, 2)))

            plt.xlabel('Wartość')
            plt.ylabel('Stopień przynależności')
            plt.tight_layout()
            plt.show()
        except ValueError:
            print("Niepoprawne argumenty. ")
    else:
        print("Niepoprawne użycie. Użyj: python main.py 2 3 4 * 2 lub 2 3 4 ^ 2")    

### Przypadek dodawania, odejmowania lub mnożenia dwóch liczb rozmytych - obsługa 7+ argumentów
# Format: lp1 śr1 pp1 operator lp2 śr2 pp2 [operator lp3 śr3 pp3] ...
elif len(sys.argv) >= 8 and (len(sys.argv) - 8) % 4 == 0:
    C = None  # Zmienna do przechowywania wyniku operacji

    # Obsługa łańcucha operacji na liczbach rozmytych
    # Gdy wykonujemy operacje na więcej niż 2 liczbach, wynik z poprzedniego działania jest przekazywany jako A,
    # Po czym program wykonuje w pętli A operator B = C, A = C
    for i in range(0, len(sys.argv)-4, 4):
        operator = sys.argv[i+4]  # Operator może być "+" (dodawanie), "-" (odejmowanie) lub "*" (mnożenie)
        if operator in ("+", "-", "*"):
            try:
                # Parametry pierwszej liczby rozmytej (A)
                lp = float(sys.argv[1])   # lewy punkt
                śr = float(sys.argv[2])   # środek (wartość z maksymalną przynależnością)
                pp = float(sys.argv[3])   # prawy punkt

                # Parametry drugiej liczby rozmytej (B)
                lp2 = float(sys.argv[i+5])  # lewy punkt
                śr2 = float(sys.argv[i+6])  # środek (wartość z maksymalną przynależnością)
                pp2 = float(sys.argv[i+7])  # prawy punkt

                # Sprawdzenie czy mamy poprawne trójkąty dla obu liczb rozmytych (lp <= śr <= pp)
                if not ((lp<=śr<=pp) and (lp2<=śr2<=pp2)):
                    raise ValueError

                # Zapobieganie sytuacji, gdy punkty są równe (dla pierwszej liczby)
                if lp==śr:
                    lp=lp-0.01
                if pp==śr:
                    pp=pp+0.01

                # Zapobieganie sytuacji, gdy punkty są równe (dla drugiej liczby)
                if lp2==śr2:
                    lp2=lp2-0.01
                if pp2==śr2:
                    pp2=pp2+0.01

                # Sprawdzenie której iteracji dotyczy obliczenie
                if(i>=4):   # Dla drugiej i kolejnych operacji (8 lub więcej argumentów)
                    A = C   # Wynik ostatniego działania jest przekazywany jako pierwsza liczba
                else:       # Pierwsza iteracja
                    # Tworzenie pierwszej liczby rozmytej A
                    A = RozmytyZbior(lp,śr,pp,np.arange(lp-0.2, pp+0.2, 0.01))

                # Tworzenie drugiej liczby rozmytej B
                B = RozmytyZbior(lp2,śr2,pp2,np.arange(lp2-0.2, pp2+0.2, 0.01))

                # Wykonanie odpowiedniej operacji na liczbach rozmytych
                if operator == "+":
                    C = A.dodaj(B)  # Dodawanie liczb rozmytych
                elif operator == "*":
                    C = A.pomnoz_przez_zbior(B)  # Mnożenie liczb rozmytych
                else:  # operator == "-"
                    C = A.odejmij(B)  # Odejmowanie liczb rozmytych


                # Wyświetlanie liczb rozmytych na wykresach
                plt.figure(figsize=(12, 4))

                # Pierwszy podwykres: liczby rozmyte A i B
                A.wyswietl(311)  # 3 wiersze, 1 kolumna, pozycja 1
                B.wyswietl(311)
                plt.title('A i B')

                # Drugi podwykres: wynik operacji (C)
                C.wyswietl(312)  # 3 wiersze, 1 kolumna, pozycja 2
                plt.title('A {} B'.format(operator))

                # Trzeci podwykres: porównanie A, B i wyniku operacji
                A.wyswietl(313)  # 3 wiersze, 1 kolumna, pozycja 3
                B.wyswietl(313)
                C.wyswietl(313)
                plt.title('A, B i A {} B'.format(operator))

                # Wypisanie parametrów liczb rozmytych: lewy punkt, środek, prawy punkt
                print("A:{:<7} {:<7} {:<7} B:{:<7} {:<7} {:<7} C:{:<7} {:<7} {:<7}".format(
                    round(A.x1, 2), round(A.m, 2), round(A.x2, 2), 
                    round(B.x1, 2), round(B.m, 2), round(B.x2, 2), 
                    round(C.x1, 2), round(C.m, 2), round(C.x2, 2)))

                plt.xlabel('Wartość')
                plt.ylabel('Stopień przynależności')
                plt.tight_layout()
                plt.show()


            except ValueError:
                print("Niepoprawne argumenty. ")
        else:
            print("Niepoprawne użycie. Użyj: python main.py 2 3 4 + 5 6 7 lub 2 3 4 - 5 6 7")

else:
    print('Niepoprawne użycie. Zła liczba argumentów. Przykłady użycia:\n'+
          'python main.py 2 3 4\n'+
          'python main.py 2 3 4 * 2\n'+
          'python main.py 2 3 4 + 5 6 7\n')
