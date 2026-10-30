# FileLens

Lokalna wyszukiwarka tekstu w dokumentach PDF dla Windows 10/11. Aplikacja indeksuje tekst w PDF-ach i przechowuje indeks lokalnie w SQLite FTS5.

## Wymagania
- Windows 10/11
- Python 3.10 lub nowszy
- PDF-y muszą zawierać warstwę tekstową. Skanowane obrazy wymagają OCR, którego jeszcze nie ma.

## Uruchomienie
Otwórz PowerShell w katalogu projektu:

```powershell
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

## Jak używać
1. Kliknij **Dodaj folder** i wybierz folder z plikami PDF (podfoldery też są przeszukiwane).
2. Kliknij **Indeksuj PDF**. Indeksowanie działa w tle.
3. Wpisz słowa lub frazę i kliknij **Szukaj**.
4. Dwuklik na wyniku otwiera oryginalny PDF.

Wyszukiwanie łączy wpisane słowa operatorem AND. Przykładowo `gwarancja pralka` znajdzie stronę zawierającą oba słowa. Wyszukiwanie ignoruje wielkość liter i normalizuje większość znaków diakrytycznych.

## Dane i prywatność
Baza indeksu jest zapisywana lokalnie w `%LOCALAPPDATA%\FileLens\index.db`. Dokumenty nie są wysyłane do sieci. Zawartość PDF jest odczytywana lokalnie.

## Ograniczenia obecnej wersji
- Brak OCR dla skanów PDF, które są wyłącznie obrazami.
- Obsługiwane są PDF-y; DOCX, XLSX i TXT dodamy w kolejnych etapach.
- Po zmianie dokumentu należy ponownie uruchomić indeksowanie jego folderu.
- Wyszukiwanie jest pełnotekstowe, nie jest jeszcze semantycznym AI.

## Licencja
MIT — zobacz plik LICENSE.
