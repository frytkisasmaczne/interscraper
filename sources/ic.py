# fumo

import json
import datetime
from requests_html import HTMLSession
import concurrent.futures


def getWholeMonth(session, depart, arrive):
	fuckingresults = []
	_today = datetime.datetime.combine(datetime.date.today(), datetime.time())
	executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
	handles = []
	for dayoffset in range(31):
		daystart = (_today + datetime.timedelta(days=dayoffset)).strftime("%Y-%m-%d %H:%M:%S")
		dayend = (_today + datetime.timedelta(days=dayoffset, hours=23, minutes=59, seconds=59)).strftime("%Y-%m-%d %H:%M:%S")
		handles.append(executor.submit(getFromTo, session, depart, arrive, daystart, dayend))
	for result in concurrent.futures.as_completed(handles):
		fuckingresults.extend(result.result())
	return sorted(fuckingresults, key=lambda fr: fr["price"])


def getFromTo(session, depart, arrive, timefrom, timeto):
	result = []

	pociagipayload = {
		"urzadzenieNr": "956",
		"metoda": "wyszukajPolaczenia",
		"dataWyjazdu": timefrom,
		"dataPrzyjazdu": timeto,
		"stacjaWyjazdu": depart,
		"stacjaPrzyjazdu": arrive,
		"stacjePrzez": [],
		"polaczeniaNajszybsze": 0,
		"liczbaPolaczen": 0,
		"czasNaPrzesiadkeMin": 3,
		"czasNaPrzesiadkeMax": 1440,
		"liczbaPrzesiadekMax": 2,
		"polaczeniaBezposrednie": 0,
		"kategoriePociagow": [],
		"kodyPrzewoznikow": [],
		"rodzajeMiejsc": [],
		"typyMiejsc": [],
		"braille": 0
	}

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
		data= json.dumps(pociagipayload)
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

		for cena in rcena.json()["ceny"]:
			if cena["cena"]:
				pricu = {
					"depart": pociag["dataWyjazdu"],
					"arrive": pociag["dataPrzyjazdu"],
					"price": cena["cena"],
					"class": cena["klasa"]
				}
				# print(pricu)
				result.append(pricu)

	return result

def stationsList(session): #[{id: 123, name: "Dupów"}]
	r = session.post("https://api-gateway.intercity.pl/server/public/endpoint/Aktualizacja",
					headers=None,
					data=json.dumps({
						"metoda": "pobierzKonfiguracje",
						"urzadzenieNr":"956"
						}))

	r = session.post("https://api-gateway.intercity.pl/server/public/endpoint/Aktualizacja", 
					headers={
						"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
						"Accept": "application/json, text/plain, */*",
						"Accept-Language": "en-US,en;q=0.5",
						"Content-Type": "application/json",
						"Sec-Fetch-Dest": "empty",
						"Sec-Fetch-Mode": "cors",
						"Sec-Fetch-Site": "same-site"
					},
					data=json.dumps({
					"metoda": "pobierzStacje",
					"ostatniaAktualizacjaData": "2024-10-03 15:36:26.026", # todo sth random an hour or so back
					"urzadzenieNr": "956"
					}))

	result = []
	for s in r.json()["stacje"]:
		id = 0
		if s["kod"] != 0:
			id = s["kod"]
		elif s["kodEPA"] != 0:
			id = s["kodEPA"]
		else:
			id = s["kodEVA"]
		result.append({"id": id, "name": s["nazwa"]})

	return result

def stationsJson(session):
	r = session.post("https://api-gateway.intercity.pl/server/public/endpoint/Aktualizacja",
					headers=None,
					data=json.dumps({"metoda":"pobierzKonfiguracje","urzadzenieNr":"956"}))

	r = session.post("https://api-gateway.intercity.pl/server/public/endpoint/Aktualizacja", 
					headers={
						"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
						"Accept": "application/json, text/plain, */*",
						"Accept-Language": "en-US,en;q=0.5",
						"Content-Type": "application/json",
						"Sec-Fetch-Dest": "empty",
						"Sec-Fetch-Mode": "cors",
						"Sec-Fetch-Site": "same-site"
					},
					data=json.dumps({
					"metoda": "pobierzStacje",
					"ostatniaAktualizacjaData": "2024-10-03 15:36:26.026", # todo sth random an hour or so back
					"urzadzenieNr": "956"
					}))

	return r.text


if __name__ == "__main__":
	session = HTMLSession()
	getWholeMonth(session, 3, 242)
