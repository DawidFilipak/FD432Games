# FD432Games

Strona studia — https://fd432games.com (GitHub Pages, gałąź `gh-pages`).

Czysty statyczny HTML/CSS, bez WordPressa i bez zależności. Dwie wersje językowe:
EN w katalogu głównym, PL pod `/pl/`.

## Jak edytować

1. Teksty i gry: [`src/content.json`](src/content.json)
   (napisy interfejsu w `ui.en` / `ui.pl`, gry w `games`).
2. Zbuduj strony:

   ```
   python src/build.py
   ```

   Skrypt nadpisuje `index.html`, `pl/…`, podstrony gier, `404.html`, `sitemap.xml`, `robots.txt`.
   Wygenerowanych plików HTML nie edytuj ręcznie.
3. Podgląd lokalny:

   ```
   python -m http.server 8432
   ```

   i otwórz http://127.0.0.1:8432/

## Dodawanie gry

- Zrzuty ekranu wrzuć do `assets/img/games/` (najlepiej `.webp`, ok. 1600 px szerokości dla poziomych, 600 px dla pionowych).
- Dodaj wpis w `games` w `content.json`:
  - `slug`: adres podstrony,
  - `status`: `released` albo `dev`,
  - `orientation`: `landscape` albo `portrait`,
  - `theme`: kolory gry; każda gra ma własny akcent, a wspólne jest logo FD,
  - `play_url`,
  - `cover`: okładka karty, najlepiej grafika promocyjna 1024×500,
  - `video`: plik z `assets/video/` i okładka filmu; może być osobny dla `en` i `pl`,
  - `shots`: lista zrzutów albo `{"en": [...], "pl": [...]}`, jeśli zrzuty są w różnych językach,
  - teksty `en` i `pl`, a w nich `shot_alts`, czyli opisy zrzutów dla czytników ekranu i Google.
- Stare adresy gry wpisz w `old_slugs`, żeby przekierowywały na nową podstronę.

## Struktura

| Ścieżka | Co to |
| --- | --- |
| `src/` | generator + treści |
| `assets/css`, `assets/js` | style i drobny JS (lightbox, zapamiętanie języka) |
| `assets/img/games/` | zrzuty ekranu gier |
| `assets/logo/` | logo SVG (znak, znak na jasne tło, logo z napisem) |
| `favicon.svg`, `favicon.ico`, `apple-touch-icon.png` | ikony |
| `app-ads.txt` | weryfikacja AdMob — **musi zostać w katalogu głównym** |
| `CNAME` | domena fd432games.com |
| `cannon-shoot-block-down-2/`, `shooting-balls-into-blocks-2/` | przekierowania ze starych adresów WordPressa |
