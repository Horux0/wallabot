import requests
from bs4 import BeautifulSoup
from telegram import Bot
import time

# === TUS DATOS DE TELEGRAM ===
TOKEN = '7783933019:AAGUwhd2GpV3GnvR3NNPD6tEkFYQ6GWoRY'
CHAT_ID = '355095466'
bot = Bot(token=TOKEN)

# === PALABRAS CLAVE ===
palabras_clave = [
    "averiado", "averiada",
    "no funciona", "no enciende", "no arranca", "no carga", "no va",
    "pantalla rota", "pantalla dañada",
    "para piezas", "para repuestos",
    "estropeado", "estropeada",
    "defectuoso", "defectuosa",
    "dañado", "dañada",
    "sin funcionar"
]

# === ENLACES YA ENVIADOS ===
enviados = set()

# === FUNCIÓN DE BÚSQUEDA ===
def buscar_wallapop():
    headers = {"User-Agent": "Mozilla/5.0"}
    nuevos = []

    for palabra in palabras_clave:
        url = f"https://es.wallapop.com/app/search?keywords={palabra.replace(' ', '%20')}"
        res = requests.get(url, headers=headers)

        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.find_all('a', href=True)

            for a in links:
                href = a['href']
                if "/item/" in href:
                    link = f"https://es.wallapop.com{href}" if href.startswith("/") else href
                    if link not in enviados:
                        nuevos.append(link)
                        enviados.add(link)

    return nuevos

# === BUCLE PRINCIPAL ===
while True:
    print("Buscando productos...")
    encontrados = buscar_wallapop()

    if encontrados:
        for link in encontrados:
            bot.send_message(chat_id=CHAT_ID, text=f"🛠 Producto averiado encontrado:\n{link}")
            print(f"Enviado: {link}")
    else:
        print("Sin novedades.")

    time.sleep(600)  # Espera 10 minutos
