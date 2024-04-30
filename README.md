# AMCEF-zadanie-scraper-repo

## Popis
Python web scraper navrhnutý na extrakciu dát z týchto všetkých [verejných zákaziek](https://www.uvo.gov.sk/vyhladavanie/vyhladavanie-zakaziek?cpv=48000000-8+72000000-5+73000000-2). Scraper získava údaje o zákazkách, ich dokumentoch a oznámeniach, ukladá tieto informácie do dictionaries/JSON súborov a tie konvertuje do [dokumentu](https://docs.google.com/spreadsheets/d/1pugWKXjA1wPkR4-OI39vCXOfgOCWjBJG3qqEzWYXjl4/edit#gid=0) v Google Sheets.

## Knižnice
Scraper používa nasledovné externé knižnice, ktoré by mali byť nainštalované:
- `aiohttp`
- `BeautifulSoup4`
- `lxml`

## Konfigurácia a spustenie
Scraper vyžaduje Python vo verzii 3.9.0 alebo vyššej. Pred spustením scraperu sa uistite, že máte nainštalované všetky potrebné knižnice:
```bash
pip install -r requirements.txt
```

### Nastavenie Google API

Pre integráciu vášho scraperu s Google Sheets je potrebné najprv nastaviť prístup k Google API a stiahnuť potrebné konfiguračné súbory. Postupujte podľa týchto krokov alebo na tomto [odkaze](https://developers.google.com/sheets/api/quickstart/python):

1. **Vytvorenie projektu v Google Cloud Console:**
   - Navštívte [Google Cloud Console](https://console.cloud.google.com/).
   - Kliknite na 'Vytvoriť projekt', zadajte názov projektu a potvrďte vytvorenie.

2. **Povolenie Google Sheets API:**
   - V dashboardu vášho projektu kliknite na 'Povoliť API a služby'.
   - Vyhľadajte 'Google Sheets API', kliknite na výsledok a potom kliknite na 'Povoliť'.

3. **Vytvorenie poverení:**
   - Po povolení API prejdite do časti 'Poverenia' v ľavom menu.
   - Kliknite na 'Vytvoriť poverenia' a vyberte 'ID klienta OAuth'.
   - Ak ešte nemáte nastavený súhlas užívateľa, systém vás vyzve k jeho konfigurácii. Vyplňte potrebné informácie.
   - Pre typ aplikácie vyberte 'Desktopová aplikácia', zadajte názov a potvrďte vytvorenie.
   - Po vytvorení ID klienta kliknite na 'Stiahnuť JSON' na stránke poverení, čím získate súbor s povereniami, ktorý potrebujete pre svoj projekt.

4. **Nastavenie `client_secret.json` v projekte:**
   - Súbor, ktorý ste stiahli, premenujte na `client_secret.json` (alebo akýkoľvek názov, ktorý používate vo svojom kóde) a umiestnite ho do adresára vášho projektu.

5. **Prvé spustenie a autorizácia:**
   - Pri prvom spustení scraperu budete vyzvaní k prihláseniu cez prehliadač.
   - Prihláste sa do Google účtu, ktorý chcete používať pre Sheets API.
   - Google vás požiada o schválenie prístupu vašej aplikácie k údajom. Po schválení bude môcť aplikácia interagovať s Google Sheets podľa konfigurovaných oprávnení.

Dodržaním týchto krokov získate potrebné poverenia a nastavíte prístup k Google Sheets pre Python scraper.

### Konfigurácia Google Sheets v projekte
Pre odosielanie dát do Google Sheets je potrebné nastaviť niekoľko konfiguračných premenných a autorizačných súborov:

1. **Google Client Secret JSON:**
   Uložte súbor s klientskými tajomstvami od Google (JSON súbor), ktorý obsahuje potrebné informácie pre autorizáciu. Meno tohto súboru je špecifikované v konfiguračnej premennej `GOOGLE_CLIENT_SECRET_JSON`.

2. **Scopes:**
   Uistite sa, že v premennej `SCOPES` sú definované všetky potrebné oprávnenia pre prístup k vašim Google Sheets. Pre tento scraper je potrebné povolenie `'https://www.googleapis.com/auth/spreadsheets'`.

3. **Spreadsheet ID a Range Name:**
   Uveďte ID a rozsah tabuľky, do ktorej chcete dáta ukladať. Tieto hodnoty sú definované v premenných `SPREADSHEET_ID` a `RANGE_NAME`.

### Proces autorizácie
Pri prvom spustení skriptu sa automaticky vytvorí súbor `token.pickle`, ktorý obsahuje tokeny pre prístup. Ak je tento súbor už existujúci ale jeho tokeny expirovali alebo nie sú platné, skript sa pokúsi token obnoviť, prípadne vyzve na nové prihlásenie.

### Spustenie
Po predošlých ktokoch, pre spustenie scraperu použite nasledovný príkaz:
```bash
python main.py
```

## Logovanie
Logy sú generované počas procesu scrapovania pre lepšie sledovanie chýb a priebehu operácií. Všetky logy sú ukladané do súboru `scraper.log`. Po každom spustení scraperu sa logy prepisujú!


## Obmedzenia

Pri používaní tohto scraperu je dôležité mať na pamäti niekoľko kľúčových obmedzení:

- **Počet Requestov:** Scraper vykonáva viac ako 22,000 HTTP requestov. Toto môže mať vplyv na čas potrebný na kompletné spracovanie a získavanie dát.

- **IP a zariadenie:** Všetky requesty sú vykonávané z jednej IP adresy/zariadenia, čo môže viesť k potenciálnym problémom s rate limitami alebo dokonca k dočasnému alebo trvalému blokovaniu IP adresy zo strany servera.

- **Rýchlosť Requestov:** Rýchlosť vykonávania requestov je obmedzená serverom, aby nedošlo k preťaženiu cieľovej stránky. Je dôležité zachovať slušné intervaly medzi requestmi, aby sme predišli blokovaniu a zároveň zabezpečili bezpečnosť dát.

- **Celkový čas:** V dôsledku vyššie uvedených obmedzení a potreby dodržiavania slušných intervalov medzi requestmi môže trvanie celého procesu scrapovania dosiahnuť približne 2555 sekúnd (43 minút).


## Možné zlepšenia

Aj keď aktuálna verzia scraperu funguje efektívne v rámci daných obmedzení, existuje niekoľko možných zlepšení, ktoré by mohli  zvýšiť výkon a efektívnosť:

1. **Použitie Proxy Serverov:**
   - Implementácia proxy serverov by mohla pomôcť zvýšiť rýchlosť requestov tým, že by sa obchádzali prípadné rate limity a obmedzenia IP adresy.

2. **Odstránenie Duplikátov:**
   - Na zdrojovej stránke sú zákazky často duplikované. Implementácia kontroly duplikátov pred ich spracovaním by mohla výrazne znížiť počet vykonaných requestov a tým aj celkovú záťaž na server a dĺžku trvania scrapovania.

3. **Ošetrenie nečakaných chýb/situácií:**
