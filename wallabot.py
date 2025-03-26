from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import time

# === TUS DATOS DE TELEGRAM ===
TOKEN = '7783933019:AAGUwhd2GpV3GnvR3NNPD6DtEkFYQG6wORY'
CHAT_ID = '355095466'

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': mensaje}
    requests.post(url, data=payload)

enviados = set()

# === Lista de palabras clave (masculino + femenino + variantes)
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

def buscar_wallapop():
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)

    for palabra in palabras_clave:
        url = f"https://es.wallapop.com/app/search?keywords={palabra}"
        print(f"🔎 Buscando: {palabra}")
        driver.get(url)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/item/')]"))
            )
            enlaces = driver.find_elements(By.XPATH, "//a[contains(@href, '/item/')]")
            nuevos = 0
            for e in enlaces:
                link = e.get_attribute("href")
                if link and link not in enviados:
                    enviados.add(link)
                    print(f"Nuevo → {link}")
                    enviar_telegram(f"📦 Producto ({palabra}):\n{link}")
                    nuevos += 1
            if nuevos == 0:
                print("Sin novedades.\n")
        except:
            print(f"❌ No se encontraron resultados para: {palabra}\n")

    driver.quit()

# 🔁 Ejecutar cada 15 minutos (900 segundos)
while True:
    buscar_wallapop()
    print("🕒 Esperando 15 minutos para la próxima búsqueda...\n")
    time.sleep(900)
