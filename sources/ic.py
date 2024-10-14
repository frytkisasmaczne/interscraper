# fumo
import string
import json
import datetime
from requests_html import HTMLSession
import concurrent.futures


def getEntireMonth(session, depart, arrive):
	fuckingresults = []
	_today = datetime.datetime.combine(datetime.date.today(), datetime.time())
	executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
	handles = []
	for dayoffset in range(31):
		daystart = (_today + datetime.timedelta(days=dayoffset)).strftime("%Y-%m-%d %H:%M:%S")
		dayend = (_today + datetime.timedelta(days=dayoffset, hours=23, minutes=59, seconds=59)).strftime("%Y-%m-%d %H:%M:%S")
		handles.append(executor.submit(getFromTo, session, depart, arrive, daystart, dayend))
	# todo just for me to notice this later. i'm thinking maybe sharing session between workers is locking them all on one mutex
	for result in concurrent.futures.as_completed(handles):
		fuckingresults.extend(result.result())
	stations = {s["id"]:s["name"] for s in stationsList(session)}
	station1 = get_koleo_name(session, stations[int(depart)])
	station2 = get_koleo_name(session, stations[int(arrive)])
	if station1 and station2:
		for result in fuckingresults:
			result["koleo"] = get_koleo_url(station1, station2, result["depart"])
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

	rpjson = rpolaczenia.json()
	if rpjson["bledy"]:
		raise Exception(rpjson)
	for polaczenie in rpjson["polaczenia"]:
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
		
		result.append({
			"id": id,
			"name": s["nazwa"],
			"abroad": (s["kod"] == 0 and s["kodEPA"] != 0)
		})

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


def get_koleo_name(session, station):
	i = station.find(" (")
	if i != -1:
		station = station[:i]
	i = station.find(".")
	if i != -1:
		station = station[:i]
	r = session.get(f"https://koleo.pl/ls?q={station}&language=pl",
              headers= {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "en-US,en;q=0.5",
                "X-CSRF-Token": "lE8eB2/2R+O6EFFK3B4nj9aPu7OibDy2aPZxHU8tvq+8o4h47i5ef8IxCu24kUMeIiNYzgKKnLhipMShb8IoAg==",
                "X-Requested-With": "XMLHttpRequest",
                "Sec-GPC": "1",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"
              }
            )
	st = sorted([st["name"] for st in r.json()["stations"]], key=lambda n: len(n))
	if st:
		m = {
			"ą": "a",
			"ć": "c",
			"ę": "e",
			"ł": "l",
			"ń": "n",
			"ó": "o",
			"ś": "s",
			"ż": "z",
			"ź": "z"
		}
		return "".join(map(lambda x: m[x] if x in m else x, st[0].lower())).replace(" ", "-")
	return False

def get_koleo_url(station1, station2, timefrom):
	# print(timefrom)
	timu = datetime.datetime.strptime(timefrom, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y_%H:%M")
	return f"https://koleo.pl/rozklad-pkp/{station1}/{station2}/{timu}/all/all"


if __name__ == "__main__":
	session = HTMLSession()
	getEntireMonth(session, 3, 242)
