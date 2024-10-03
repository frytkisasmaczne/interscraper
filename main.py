# fumo

import json
import datetime
from requests_html import HTMLSession

fuckingresults = []

session = HTMLSession()
_today = datetime.datetime.combine(datetime.date.today(), datetime.time())
for dayoffset in range(31):
	daystart = (_today + datetime.timedelta(days=dayoffset)).strftime("%Y-%m-%d %H:%M:%S")
	dayend = (_today + datetime.timedelta(days=dayoffset, hours=23, minutes=59, seconds=59)).strftime("%Y-%m-%d %H:%M:%S")
	
	pociagipayload = {'urzadzenieNr': '956', 'metoda': 'wyszukajPolaczenia', 'dataWyjazdu': daystart, 'dataPrzyjazdu': dayend, 'stacjaWyjazdu': 5196003, 'stacjaPrzyjazdu': 3, 'stacjePrzez': [], 'polaczeniaNajszybsze': 0, 'liczbaPolaczen': 0, 'czasNaPrzesiadkeMin': 3, 'czasNaPrzesiadkeMax': 1440, 'liczbaPrzesiadekMax': 2, 'polaczeniaBezposrednie': 0, 'kategoriePociagow': [], 'kodyPrzewoznikow': [], 'rodzajeMiejsc': [], 'typyMiejsc': [], 'braille': 0}
	
	rpolaczenia = session.post( "https://api-gateway.intercity.pl/server/public/endpoint/Pociagi",
		headers= {
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
			"Accept": "application/json, text/plain, */*",
			"Accept-Language": "en-US,en;q=0.5",
			"Content-Type": "application/json",
			"Sec-Fetch-Dest": "empty",
			"Sec-Fetch-Mode": "cors",
			"Sec-Fetch-Site": "same-site",
			"Pragma": "no-cache",
			"Cache-Control": "no-cache"
		},
		data= json.dumps(pociagipayload),
	)

	for polaczenie in rpolaczenia.json()["polaczenia"]:
		# filtrowanie po dostepnych miejscach chyba z polaczenie["typyMiejsc"]
		cenapayload = {
			"jezyk": "EN",
			"metoda": "sprawdzCene",
			"odcinki": [],
			"ofertaKod": 1,
			"podrozni": [
				{
					"kodZakupowyZnizki": 1010
				}
			],
			"urzadzenieNr": "956"
		}
		for pociag in polaczenie["pociagi"]:
			cenapayload["odcinki"].append({
					"pociagNr": pociag["nrPociagu"],
					"stacjaDoKod": pociag["stacjaPrzyjazdu"],
					"stacjaOdKod": pociag["stacjaWyjazdu"],
					"wyjazdData": pociag["dataWyjazdu"]
				})

		rcena = session.post( "https://api-gateway.intercity.pl/server/public/endpoint/Sprzedaz",
			headers= {
				"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
				"Accept": "application/json, text/plain, */*",
				"Accept-Language": "en-US,en;q=0.5",
				"Content-Type": "application/json",
				"Sec-Fetch-Dest": "empty",
				"Sec-Fetch-Mode": "cors",
				"Sec-Fetch-Site": "same-site"
			},
			data= json.dumps(cenapayload),
		)

		# print("\n", rcena.json())

		for cena in rcena.json()["ceny"]:
			if cena["cena"]:
				fuckingresults.append({
					"depart": pociag["dataWyjazdu"],
					"arrive": pociag["dataPrzyjazdu"],
					"price": cena["cena"]
				})
				print(fuckingresults[-1])


print(fuckingresults)

	# quit()
