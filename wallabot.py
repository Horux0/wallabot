from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import requests
import os
import re
from datetime import datetime, timedelta
import random
from selenium.common.exceptions import TimeoutException
import threading
import signal
import sys
import csv
import numpy as np
from collections import defaultdict
import hashlib

# === CONFIGURACIÓN TELEGRAM ===
TOKEN = '7783933019:AAGUwhd2GpV3GnvR3NNPD6DtEkFYQG6wORY'
CHAT_ID = '355095466'

# === ARCHIVOS PARA SEGUIMIENTO ===
HISTORIAL_FILE = 'wallabot_historial.json'
PRECIOS_DB_FILE = 'wallabot_precios_db.json'
CATEGORIAS_FILE = 'wallabot_categorias.json'
CONFIG_FILE = 'wallabot_config.json'
LOG_FILE = 'wallabot_log.txt'

# === MODOS DE BÚSQUEDA ===
MODO_AVERIADOS = "averiados"  # Productos averiados/para piezas
MODO_CHOLLOS = "chollos"      # Productos con precio anormalmente bajo
MODO_TODOS = "todos"          # Ambos tipos

# === UMBRAL PARA DETECTAR CHOLLOS ===
# Porcentaje mínimo de diferencia para considerar un chollo
UMBRAL_CHOLLO_PORCENTAJE = 40  # Precio al menos 40% por debajo del precio medio

# === CONFIGURACIÓN PREDETERMINADA ===
CONFIG_PREDETERMINADA = {
    "precio_maximo": 300,
    "precio_minimo": 5,
    "umbral_chollo": 40,
    "tiempo_espera": 900,  # 15 minutos
    "modo_busqueda": MODO_TODOS,
    "max_items_por_busqueda": 50,
    "filtrar_ubicacion": False,
    "ubicaciones_preferidas": ["Madrid", "Barcelona", "Valencia"],
    "notificacion_sonido": True,
    "max_intentos": 3,
    "busqueda_inteligente": True,
    "enviados_max_dias": 30  # Días para mantener historial
}

# === PALABRAS CLAVE PARA BÚSQUEDA ===
# Palabras clave para productos averiados
palabras_clave_averiados = [
    "averiado", "averiada", "no funciona", "no enciende", "no arranca",
    "no carga", "no va", "pantalla rota", "pantalla dañada", "pantalla agrietada",
    "para piezas", "para repuestos", "estropeado", "estropeada", "roto", "rota",
    "defectuoso", "defectuosa", "dañado", "dañada", "sin funcionar", "bateria rota",
    "no se que le pasa", "dejo de funcionar", "no se muy bien", "no responde",
    "se apaga", "pierde carga", "fallo", "tiene un fallo", "tiene un problema",
    "a reparar", "necesita reparación", "para arreglar", "necesita arreglar",
    "a medias", "se calienta", "sin batería", "tiene un golpe", "con golpe",
    "sin cargar", "error", "da error"
]

# Palabras que NO interesan (filtro negativo)
palabras_excluidas = [
    # Contenido y entretenimiento físico
    "libro", "novela", "revista", "poesía", "cuentos", "diccionario",
    "muñeco", "muñeca", "juguete", "lego", "playmobil", "peluche",
    "disco", "vinilo", "cd", "dvd", "bluray", "película",
    "figura", "colección", "álbum", "cromos", "tebeo", "cómic",
    "puzzle", "juego de mesa", "baraja", "cartas",
    
    # Ropa y accesorios baratos
    "camiseta", "sudadera", "vestido", "pantalón", "calzado", "zapatos",
    "zapatillas", "bolso", "mochila", "cartera", "gorra", "sombrero",
    
    # Cosmética y belleza
    "perfume", "colonia", "maquillaje", "esmalte", "pintauñas", "crema",
    
    # Artículos de bajo valor
    "llavero", "bolígrafo", "adorno", "decoración", "póster", "taza",
    "vajilla", "cubiertos", "mantel", "cortina", "alfombra",
    
    # Consumibles
    "tinta", "tóner", "recambio", "repuesto", "pilas", "batería recargable",
    
    # Otros
    "limpieza", "accesorio", "funda", "carcasa", "protector"
]

# Palabras que SÍ interesan (filtro positivo) - Ampliado
palabras_deseadas = [
    # Tecnología y electrónica
    "portátil", "laptop", "notebook", "pantalla", "monitor", "tablet", 
    "móvil", "iphone", "samsung", "huawei", "xiaomi", "oppo", "oneplus", "realme", "poco",
    "ps4", "ps5", "playstation", "nintendo", "switch", "xbox", "consola", "gaming",
    "ordenador", "pc", "torre", "sobremesa", "imac", "mac", "macbook", "apple", "chromebook",
    "altavoz", "router", "impresora", "escáner", "multifunción", "plotter",
    "cámara", "sony", "canon", "nikon", "gopro", "reflex", "mirrorless", "dron", "gimbal",
    "cpu", "gpu", "rtx", "gtx", "amd", "ryzen", "intel", "procesador", "tarjeta gráfica",
    "arduino", "raspberry", "microcontrolador", "domótica", "alexa", "google home",
    
    # Audio y sonido
    "altavoces", "auriculares", "airpods", "homepod", "bluetooth", "subwoofer", "barra de sonido",
    "amplificador", "dac", "tocadiscos", "vinilo", "micrófono", "beats", "bose", "sonos", "jbl",
    
    # Almacenamiento
    "disco duro", "ssd", "memoria", "nvme", "pendrive", "usb", "microsd", "nas", "servidor",
    
    # Electrodomésticos
    "microondas", "lavadora", "secadora", "lavavajillas", "frigorífico", "nevera", "congelador",
    "horno", "vitrocerámica", "inducción", "robot aspirador", "roomba", "robot cocina", "thermomix",
    "cafetera", "nespresso", "batidora", "tostadora", "freidora aire", "airfryer", "vaporera",
    "climatizador", "aire acondicionado", "ventilador", "calefactor", "radiador", "purificador",
    
    # Fotografía y vídeo
    "objetivo", "lente", "flash", "trípode", "estabilizador", "filtro", "iluminación", "estudio",
    
    # Relojes inteligentes y wearables
    "smartwatch", "reloj inteligente", "apple watch", "fitbit", "garmin", "amazfit", "pulsera actividad",
    
    # Instrumentos musicales
    "guitarra", "piano", "teclado", "batería", "sintetizador", "bajo", "amplificador", "pedal",
    
    # Herramientas
    "taladro", "destornillador", "sierra", "lijadora", "dremel", "soldador", "compresor", "bosch",
    "makita", "dewalt", "stanley", "herramienta eléctrica", "multiherramienta", "nivel láser",
    
    # Muebles y decoración valiosos
    "sillón", "sofá", "escritorio", "mesa", "silla", "ergonómica", "lámpara", "diseño",
    
    # Bicicletas y movilidad
    "bicicleta", "patinete eléctrico", "xiaomi", "segway", "scooter", "ebike", "mountain bike", "mtb",
    
    # Dispositivos médicos y salud
    "tens", "masajeador", "báscula", "tensiómetro", "termómetro", "nebulizador", "cpap",
    
    # Marcas premium adicionales
    "dyson", "philips", "lg", "panasonic", "samsung", "siemens", "bosch", "miele", "smeg", "aeg",
    "asus", "acer", "lenovo", "msi", "razer", "logitech", "corsair", "hyperx"
]

# === CATEGORÍAS PARA BÚSQUEDA INTELIGENTE ===
CATEGORIAS_PRECIOS = {
    "smartphones": {
        "keywords": ["iphone", "móvil", "smartphone", "teléfono", "samsung galaxy", "xiaomi", "huawei", "oneplus"],
        "precios": {
            "gama_baja": {"min": 50, "max": 150, "nombre": "Gama baja"},
            "gama_media": {"min": 150, "max": 400, "nombre": "Gama media"},
            "gama_alta": {"min": 400, "max": 800, "nombre": "Gama alta"},
            "premium": {"min": 800, "max": 1500, "nombre": "Premium"}
        }
    },
    "portatiles": {
        "keywords": ["portátil", "laptop", "notebook", "macbook", "chromebook"],
        "precios": {
            "basico": {"min": 150, "max": 400, "nombre": "Básico"},
            "medio": {"min": 400, "max": 800, "nombre": "Medio"},
            "avanzado": {"min": 800, "max": 1500, "nombre": "Avanzado"},
            "premium": {"min": 1500, "max": 3000, "nombre": "Premium"}
        }
    },
    "consolas": {
        "keywords": ["ps4", "ps5", "xbox", "nintendo switch", "playstation", "consola"],
        "precios": {
            "generacion_anterior": {"min": 100, "max": 250, "nombre": "Generación anterior"},
            "actual": {"min": 250, "max": 600, "nombre": "Actual"}
        }
    },
    "tablets": {
        "keywords": ["tablet", "ipad", "galaxy tab", "huawei matepad"],
        "precios": {
            "basica": {"min": 50, "max": 200, "nombre": "Básica"},
            "media": {"min": 200, "max": 500, "nombre": "Media"},
            "premium": {"min": 500, "max": 1200, "nombre": "Premium"}
        }
    }
}

# === FUNCIONES AUXILIARES ===
def cargar_configuracion():
    """Carga la configuración desde el archivo JSON o utiliza la predeterminada"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log_actividad(f"Error al cargar configuración: {e}")
            return CONFIG_PREDETERMINADA
    else:
        # Si no existe el archivo, guardar la configuración predeterminada
        guardar_configuracion(CONFIG_PREDETERMINADA)
        return CONFIG_PREDETERMINADA

def guardar_configuracion(config):
    """Guarda la configuración en un archivo JSON"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        log_actividad(f"Error al guardar configuración: {e}")

def cargar_historial():
    """Carga los enlaces ya visitados desde un archivo JSON"""
    if os.path.exists(HISTORIAL_FILE):
        try:
            with open(HISTORIAL_FILE, 'r', encoding='utf-8') as f:
                historial = json.load(f)
                
                # Convertir historial antiguo (solo URLs) al nuevo formato
                if isinstance(historial, list):
                    nuevo_historial = {}
                    for url in historial:
                        nuevo_historial[url] = {
                            "fecha": datetime.now().isoformat(),
                            "tipo": "desconocido"
                        }
                    return nuevo_historial
                return historial
        except Exception as e:
            log_actividad(f"Error al cargar historial: {e}")
            return {}
    return {}

def limpiar_historial_antiguo(historial, dias=30):
    """Elimina entradas más antiguas que el número de días especificado"""
    if not historial:
        return {}
    
    limite = (datetime.now() - timedelta(days=dias)).isoformat()
    nuevo_historial = {}
    
    for url, datos in historial.items():
        if "fecha" in datos and datos["fecha"] >= limite:
            nuevo_historial[url] = datos
    
    return nuevo_historial

def guardar_historial(historial):
    """Guarda el historial de productos visitados en un archivo JSON"""
    try:
        with open(HISTORIAL_FILE, 'w', encoding='utf-8') as f:
            json.dump(historial, f, ensure_ascii=False, indent=4)
    except Exception as e:
        log_actividad(f"Error al guardar historial: {e}")

def cargar_precios_db():
    """Carga la base de datos de precios de referencia"""
    if os.path.exists(PRECIOS_DB_FILE):
        try:
            with open(PRECIOS_DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log_actividad(f"Error al cargar base de datos de precios: {e}")
            return {}
    return {}

def guardar_precios_db(precios_db):
    """Guarda la base de datos de precios de referencia"""
    try:
        with open(PRECIOS_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(precios_db, f, ensure_ascii=False, indent=4)
    except Exception as e:
        log_actividad(f"Error al guardar base de datos de precios: {e}")

def enviar_telegram(mensaje, url_producto=None, usar_markdown=False):
    """Envía un mensaje a través de Telegram con botones si se proporciona una URL"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': mensaje
    }

    if usar_markdown:
        payload['parse_mode'] = 'Markdown'

    if url_producto:
        payload['reply_markup'] = json.dumps({
            "inline_keyboard": [
                [
                    {
                        "text": "❌ No me interesa",
                        "callback_data": f"descartar|{url_producto}"
                    },
                    {
                        "text": "🤔 Puede interesar",
                        "callback_data": f"dudoso|{url_producto}"
                    },
                    {
                        "text": "👍 Me interesa",
                        "callback_data": f"interesa|{url_producto}"
                    }
                ]
            ]
        })

    try:
        requests.post(url, data=payload)
    except Exception as e:
        log_actividad(f"Error al enviar mensaje a Telegram: {e}")

def extraer_precio(texto):
    """Extrae el precio del texto del anuncio"""
    # Asegurarse de que texto sea una cadena
    if not isinstance(texto, str):
        return None
        
    precio_match = re.search(r'(\d+(?:[.,]\d+)?)\s*€', texto)
    if precio_match:
        precio_str = precio_match.group(1).replace(',', '.')
        try:
            return float(precio_str)
        except ValueError:
            return None
    return None
    
def generar_id_callback(link):
    return hashlib.md5(link.encode()).hexdigest()[:10]  # ID de 10 caracteres
    
def enviar_producto_con_botones(producto_info, mensaje):
    """Envía un mensaje con botones 👍👎 para obtener feedback del usuario."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    id_callback = generar_id_callback(producto_info["link"])

    botones = {
        "inline_keyboard": [[
            {"text": "👍 Me interesa", "callback_data": f"like|{id_callback}"},
            {"text": "👎 No me interesa", "callback_data": f"dislike|{id_callback}"},
            {"text": "🤔 Puede interesar", "callback_data": f"maybe|{id_callback}"}
        ]]
    }

    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "reply_markup": json.dumps(botones),
        "parse_mode": "HTML"  # Evita problemas con el markdown
    }

    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            log_actividad(f"❌ Telegram rechazó el mensaje: {response.text}")
    except Exception as e:
        log_actividad(f"Error al enviar producto con botones: {e}")


def obtener_modelo_producto(texto, titulo):
    """Intenta extraer el modelo del producto del título o descripción"""
    # Asegurarse de que texto y titulo sean cadenas
    texto = str(texto) if texto is not None else ""
    titulo = str(titulo) if titulo is not None else ""
    
    texto_completo = (texto + " " + titulo).lower()
    
    # Patrones comunes para modelos de productos
    patrones = [
        r'(iphone\s*\d+(?:\s*(?:pro|max|plus|mini|x|xs|xr|se))?)',
        r'(galaxy\s*(?:s|note|a|j|m|z|fold)\d+(?:\s*(?:plus|ultra|fe))?)',
        r'(macbook\s*(?:pro|air)?\s*\d+(?:\.\d+)?(?:\s*(?:inch|pulgadas))?)',
        r'(playstation\s*[45]|ps[45])',
        r'(xbox\s*(?:one|series\s*(?:x|s)))',
        r'(switch\s*(?:lite|oled)?)',
        r'(inspiron|xps|pavilion|ideapad|thinkpad|envy|spectre|legion|rog)\s*\d+',
        r'(ryzen\s*\d+(?:\s*\d+)?(?:\s*x)?)',
        r'(core\s*i[3579](?:\-\d+)?)',
        r'(rtx\s*\d+(?:\s*ti)?)',
        r'(gtx\s*\d+(?:\s*ti)?)'
    ]
    
    for patron in patrones:
        match = re.search(patron, texto_completo)
        if match:
            return match.group(1)
    
    # Si no se encuentra un modelo específico, intentar extraer marca + tipo producto
    marcas = ["samsung", "apple", "xiaomi", "sony", "lg", "huawei", "lenovo", "asus", 
             "acer", "hp", "dell", "msi", "canon", "nikon", "philips", "logitech", "bosch"]
    
    tipos = ["televisor", "monitor", "portátil", "laptop", "móvil", "smartphone", 
            "tablet", "cámara", "consola", "altavoz", "impresora", "auriculares"]
    
    for marca in marcas:
        if marca in texto_completo:
            for tipo in tipos:
                if tipo in texto_completo:
                    return f"{marca} {tipo}"
            return marca
    
    # Devolver categoría general si no se encuentra nada específico
    for tipo in tipos:
        if tipo in texto_completo:
            return tipo
    
    return None

def categorizar_producto(texto, titulo):
    """Categoriza el producto para comparar con precios de referencia adecuados"""
    # Asegurarse de que texto y titulo sean cadenas
    texto = str(texto) if texto is not None else ""
    titulo = str(titulo) if titulo is not None else ""
    
    texto_completo = (texto + " " + titulo).lower()
    
    for categoria, info in CATEGORIAS_PRECIOS.items():
        for keyword in info["keywords"]:
            if keyword.lower() in texto_completo:
                return categoria
    
    return "general"

def estimar_precio_normal(producto_info, precios_db):
    """Estima el precio 'normal' de un producto usando la base de datos de precios"""
    if not producto_info or not precios_db:
        return None
    
    modelo = producto_info.get("modelo")
    categoria = producto_info.get("categoria", "general")
    
    # Comprobar por modelo específico
    if modelo and modelo in precios_db:
        precios = [p for p in precios_db[modelo]["precios"] if p > 0]
        if precios:
            # Usar media recortada para evitar valores extremos
            precios.sort()
            recorte = max(1, len(precios) // 5)
            precios_filtrados = precios[recorte:-recorte] if len(precios) > 5 else precios
            return sum(precios_filtrados) / len(precios_filtrados)
    
    # Comprobar por categoría
    if categoria in CATEGORIAS_PRECIOS:
        # Intentar adivinar la gama basándonos en patrones conocidos
        for gama, rango in CATEGORIAS_PRECIOS[categoria]["precios"].items():
            min_precio = rango["min"]
            max_precio = rango["max"]
            
            # Si tenemos información específica del modelo, comparar con rangos predefinidos
            if producto_info.get("precio_ultimo") and min_precio <= producto_info["precio_ultimo"] <= max_precio:
                return producto_info["precio_ultimo"]
    
    # Si no hay suficiente información, devolver None
    return None

def calcular_descuento(precio_actual, precio_estimado):
    """Calcula el porcentaje de descuento entre dos precios"""
    if not precio_actual or not precio_estimado or precio_estimado <= 0:
        return 0
    
    return ((precio_estimado - precio_actual) / precio_estimado) * 100

def es_chollo(producto_info, precios_db, config):
    """Determina si un producto es un chollo basado en su precio y historial"""
    if not producto_info or not precios_db:
        return False, 0, None
    
    precio_actual = producto_info.get("precio")
    if not precio_actual or precio_actual <= 0:
        return False, 0, None
    
    # Comprobar límites de precio
    if precio_actual < config["precio_minimo"] or precio_actual > config["precio_maximo"]:
        return False, 0, None
    
    # Calcular precio de referencia
    precio_estimado = estimar_precio_normal(producto_info, precios_db)
    
    if not precio_estimado:
        return False, 0, None
    
    # Calcular porcentaje de descuento
    porcentaje_descuento = calcular_descuento(precio_actual, precio_estimado)
    
    # Determinar si el descuento supera el umbral para considerarlo chollo
    es_chollo = porcentaje_descuento >= config["umbral_chollo"]
    
    return es_chollo, porcentaje_descuento, precio_estimado

def actualizar_precios_db(precios_db, producto_info):
    """Actualiza la base de datos de precios con un nuevo producto observado"""
    if not producto_info or "modelo" not in producto_info or "precio" not in producto_info:
        return precios_db
    
    modelo = producto_info["modelo"]
    precio = producto_info["precio"]
    
    if precio <= 0:
        return precios_db
    
    # Limitar tamaño de historial de precios
    max_precios_por_modelo = 100
    
    if modelo not in precios_db:
        precios_db[modelo] = {
            "categoria": producto_info.get("categoria", "general"),
            "precios": [precio],
            "fechas": [datetime.now().isoformat()]
        }
    else:
        # Añadir nuevo precio al historial
        precios_db[modelo]["precios"].append(precio)
        precios_db[modelo]["fechas"].append(datetime.now().isoformat())
        
        # Limitar tamaño
        if len(precios_db[modelo]["precios"]) > max_precios_por_modelo:
            precios_db[modelo]["precios"] = precios_db[modelo]["precios"][-max_precios_por_modelo:]
            precios_db[modelo]["fechas"] = precios_db[modelo]["fechas"][-max_precios_por_modelo:]
    
    return precios_db

def texto_valido(texto, titulo, config):
    """Verifica si el texto y título son válidos según los filtros configurados"""
    # Asegurarse de que texto y titulo sean cadenas
    texto = str(texto) if texto is not None else ""
    titulo = str(titulo) if titulo is not None else ""
    
    texto_completo = (texto + " " + titulo).lower()
    
    # Si contiene alguna palabra excluida, rechazar
    if any(p.lower() in texto_completo for p in palabras_excluidas):
        return False, None
    
    # Filtrar por ubicación si está activado
    if config["filtrar_ubicacion"]:
        ubicacion_encontrada = False
        for ubicacion in config["ubicaciones_preferidas"]:
            if ubicacion.lower() in texto_completo:
                ubicacion_encontrada = True
                break
        if not ubicacion_encontrada:
            return False, None
    
    # Detectar si es producto averiado
    es_averiado = False
    if any(p.lower() in texto_completo for p in palabras_clave_averiados):
        es_averiado = True
    
    # Si contiene alguna palabra deseada, aceptar
    if any(p.lower() in texto_completo for p in palabras_deseadas):
        return True, MODO_AVERIADOS if es_averiado else MODO_CHOLLOS
    
    # Si no cumple los criterios anteriores, rechazar
    return False, None

def log_actividad(mensaje):
    """Registra actividad en un archivo de log con fecha y hora"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {mensaje}\n")
        print(f"[{timestamp}] {mensaje}")
    except Exception as e:
        print(f"Error al escribir en log: {e}")

def formatear_mensaje_chollo(producto_info, porcentaje_descuento=None, precio_estimado=None, tipo=None):
    """Formatea un mensaje para enviar a Telegram con información del chollo"""
    if tipo == MODO_AVERIADOS:
        emoji = "🔧"
        tipo_texto = "averiado"
    else:
        emoji = "💰"
        tipo_texto = "a precio de chollo"
    
    mensaje = f"{emoji} Posible {tipo_texto}:\n"
    mensaje += f"📱 {producto_info['titulo'].strip()}\n"
    mensaje += f"💸 {producto_info['precio']}€\n"
    
    if porcentaje_descuento and precio_estimado:
        mensaje += f"📉 Descuento estimado: {porcentaje_descuento:.1f}% (precio normal ~{precio_estimado:.2f}€)\n"
    
    if "ubicacion" in producto_info and producto_info["ubicacion"]:
        mensaje += f"📍 {producto_info['ubicacion']}\n"
    
    mensaje += f"🔗 {producto_info['link']}"
    
    return mensaje

# === FUNCIONES PRINCIPALES ===
def procesar_elemento(elemento, historial, precios_db, config):
    """Procesa un elemento de Wallapop y determina si es relevante"""
    try:
        # Extraer enlace del producto
        link = elemento.get_attribute("href")
        if not link or link in historial:
            return None, False
            
        # Extraer título, precio, descripción y ubicación
        titulo = elemento.text
        
        # Intentar obtener descripción si está disponible
        descripcion = ""
        try:
            desc_elem = elemento.find_element(By.XPATH, ".//p[@class='ItemCard__description']")
            if desc_elem:
                descripcion = desc_elem.text
        except:
            pass  # Si no hay descripción, seguimos
        
        # Intentar obtener ubicación
        ubicacion = ""
        try:
            ubicacion_elem = elemento.find_element(By.XPATH, ".//span[contains(@class, 'ItemCard__location')]")
            if ubicacion_elem:
                ubicacion = ubicacion_elem.text
        except:
            pass
        
        # Verificar si el texto cumple los criterios
        valido, tipo_producto = texto_valido(descripcion, titulo, config)
        
        if not valido:
            return None, False
        
        # Obtener precio numérico
        precio = extraer_precio(titulo)
        
        if precio is None:
            return None, False
        
        # Filtrar por precio límite configurado
        if precio < config["precio_minimo"] or precio > config["precio_maximo"]:
            return None, False
        
        # Identificar modelo y categoría
        modelo = obtener_modelo_producto(descripcion, titulo)
        categoria = categorizar_producto(descripcion, titulo)
        
        # Crear información del producto
        producto_info = {
            "link": link,
            "titulo": titulo,
            "descripcion": descripcion,
            "precio": precio,
            "modelo": modelo,
            "categoria": categoria,
            "ubicacion": ubicacion,
            "tipo": tipo_producto
        }
        
        # Verificar si es producto a procesar según el modo configurado
        if config["modo_busqueda"] == MODO_AVERIADOS and tipo_producto != MODO_AVERIADOS:
            return None, False
        
        if config["modo_busqueda"] == MODO_CHOLLOS and tipo_producto == MODO_AVERIADOS:
            return None, False
        
        # Si es un posible chollo por precio, verificarlo
        es_chollazo = False
        porcentaje_descuento = 0
        precio_estimado = None
        
        if tipo_producto != MODO_AVERIADOS:
            es_chollazo, porcentaje_descuento, precio_estimado = es_chollo(producto_info, precios_db, config)
            if not es_chollazo:
                return None, False
        
        # Si llegamos aquí, el producto es interesante
        return {
            "producto": producto_info,
            "es_chollazo": es_chollazo,
            "porcentaje_descuento": porcentaje_descuento,
            "precio_estimado": precio_estimado
        }, True
            
    except Exception as e:
        log_actividad(f"Error procesando elemento: {str(e)}")
        return None, False

def buscar_wallapop(config, driver=None): 
    """Busca productos interesantes en Wallapop"""
    # Configurar el navegador si no se proporciona uno
    navegador_interno = False
    if driver is None:
        options = Options() 
        options.headless = True
        
        # Configuración adicional para evitar detección como bot
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Intenta usar Chrome si Firefox da problemas
        try:
            driver = webdriver.Firefox(options=options)
        except Exception as e:
            log_actividad(f"Error al iniciar Firefox: {e}. Intentando con Chrome...")
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            chrome_options = ChromeOptions()
            chrome_options.add_argument(f'user-agent={user_agent}')
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--headless")
            driver = webdriver.Chrome(options=chrome_options)
            
        driver.set_window_size(1920, 1080)
        navegador_interno = True
    
    # Cargar historial, base de datos de precios
    historial = cargar_historial()
    precios_db = cargar_precios_db()
    
    # Limpiar historial antiguo
    historial = limpiar_historial_antiguo(historial, config["enviados_max_dias"])
    
    total_nuevos = 0
    
    try:
        # Lista de palabras clave a buscar según modo
        palabras_busqueda = []
        
        if config["modo_busqueda"] in [MODO_AVERIADOS, MODO_TODOS]:
            palabras_busqueda.extend(palabras_clave_averiados)
        
        if config["modo_busqueda"] in [MODO_CHOLLOS, MODO_TODOS]:
            # Buscar por categorías y marcas populares para encontrar chollos
            chollos_busqueda = [
                "iphone", "samsung", "xiaomi", "playstation", "nintendo", 
                "portatil gaming", "apple", "macbook", "televisor", "ordenador gaming",
                "tablet", "silla gaming", "monitor", "camara", "gopro", "patinete electrico"
            ]
            palabras_busqueda.extend(chollos_busqueda)
        
        # Eliminar duplicados
        palabras_busqueda = list(set(palabras_busqueda))
        
        # Búsqueda de productos
        for palabra in palabras_busqueda:
            # Configurar rango de precios en la URL
            rango_precios = f"&min_sale_price={config['precio_minimo']}&max_sale_price={config['precio_maximo']}"
            
            # Construir URL de búsqueda
            url = f"https://es.wallapop.com/app/search?keywords={palabra}{rango_precios}&order_by=newest"
            
            log_actividad(f"🔎 Buscando: {palabra}")
            driver.get(url)
            
            # Esperar a que cargue la página
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/item/')]"))
                )
                
                # Desplazamiento para cargar más resultados
                for _ in range(3):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.5)
                
                # Recopilar información de artículos
                elementos = driver.find_elements(By.XPATH, "//a[contains(@href, '/item/')]")
                log_actividad(f"🔍 Elementos encontrados: {len(elementos)}")
                nuevos = 0
                
                # Limitar número de elementos a procesar
                elementos = elementos[:config["max_items_por_busqueda"]]
                
                for e in elementos:
                    # Procesar elemento y verificar si es interesante
                    resultado, es_interesante = procesar_elemento(e, historial, precios_db, config)
                    
                    if es_interesante and resultado:
                        producto_info = resultado["producto"]
                        link = producto_info["link"]
                        
                        # Registrar en historial
                        historial[link] = {
                            "fecha": datetime.now().isoformat(),
                            "tipo": producto_info["tipo"],
                            "precio": producto_info["precio"]
                        }
                        
                        # Actualizar base de datos de precios
                        precios_db = actualizar_precios_db(precios_db, producto_info)
                        
                        # Formatear mensaje según tipo
                        if producto_info["tipo"] == MODO_AVERIADOS:
                            mensaje = formatear_mensaje_chollo(producto_info, tipo=MODO_AVERIADOS)
                        else:
                            mensaje = formatear_mensaje_chollo(
                                producto_info, 
                                resultado["porcentaje_descuento"],
                                resultado["precio_estimado"],
                                MODO_CHOLLOS
                            )
                        
                        log_actividad(f"✅ Nuevo → {producto_info['titulo']} ({producto_info['precio']}€)")
                        log_actividad(f"[DEBUG] Intentando enviar producto: {producto_info}")
                        log_actividad(f"[DEBUG] Mensaje generado: {mensaje}")
                        enviar_producto_con_botones(producto_info, mensaje)
                        nuevos += 1
                        total_nuevos += 1
                        
                        # Guardar historial cada 5 nuevos elementos para evitar pérdidas
                        if nuevos % 5 == 0:
                            guardar_historial(historial)
                            guardar_precios_db(precios_db)
                                
                if nuevos == 0:
                    log_actividad(f"Sin novedades para '{palabra}'")
                else:
                    log_actividad(f"Se encontraron {nuevos} productos nuevos para '{palabra}'")
                    
            except TimeoutException:
                log_actividad(f"⚠️ Timeout esperando resultados para '{palabra}'")
            except Exception as e:
                log_actividad(f"❌ Error buscando '{palabra}': {str(e)}")
            
            # Pausa entre búsquedas para evitar ser bloqueado
            time.sleep(random.uniform(2, 4))
            
    except Exception as e:
        log_actividad(f"❌ Error general: {str(e)}")
    finally:
        # Cerrar navegador si fue creado internamente
        if navegador_interno:
            driver.quit()
            
        # Guardar historial y base de datos al finalizar
        guardar_historial(historial)
        guardar_precios_db(precios_db)
        log_actividad(f"🔄 Historial actualizado: {len(historial)} productos en total")
        
    return total_nuevos

def generar_estadisticas(historial, precios_db):
    """Genera estadísticas sobre los productos encontrados"""
    if not historial:
        return "No hay suficientes datos para generar estadísticas."
    
    # Contar por tipo
    conteo_tipos = defaultdict(int)
    conteo_por_dia = defaultdict(int)
    
    for url, datos in historial.items():
        tipo = datos.get("tipo", "desconocido")
        conteo_tipos[tipo] += 1
        
        # Estadísticas por día
        if "fecha" in datos:
            fecha = datos["fecha"].split("T")[0]  # Extraer solo YYYY-MM-DD
            conteo_por_dia[fecha] += 1
    
    # Ordenar días cronológicamente
    dias_ordenados = sorted(conteo_por_dia.keys())
    
    # Generar texto de estadísticas
    stats = "📊 ESTADÍSTICAS DE WALLABOT CAZACHOLLOS 📊\n\n"
    stats += f"Total de productos registrados: {len(historial)}\n\n"
    stats += "Por tipo:\n"
    
    for tipo, conteo in conteo_tipos.items():
        tipo_nombre = "Averiados" if tipo == MODO_AVERIADOS else "Chollos de precio"
        if tipo == "desconocido":
            tipo_nombre = "Sin clasificar"
        stats += f"- {tipo_nombre}: {conteo}\n"
    
    stats += "\nActividad reciente:\n"
    
    # Mostrar solo los últimos 7 días o todos si hay menos
    dias_mostrar = dias_ordenados[-7:] if len(dias_ordenados) > 7 else dias_ordenados
    
    for dia in dias_mostrar:
        stats += f"- {dia}: {conteo_por_dia[dia]} productos\n"
    
    # Estadísticas de base de datos de precios
    if precios_db:
        stats += f"\nBase de datos de precios:\n"
        stats += f"- Modelos registrados: {len(precios_db)}\n"
        
        # Top 5 modelos con más datos
        modelos_por_datos = sorted(precios_db.items(), key=lambda x: len(x[1]["precios"]), reverse=True)[:5]
        
        if modelos_por_datos:
            stats += "- Top 5 modelos con más datos:\n"
            for modelo, datos in modelos_por_datos:
                stats += f"  * {modelo}: {len(datos['precios'])} registros\n"
    
    return stats

def comando_estadisticas():
    """Genera y envía estadísticas al chat de Telegram"""
    historial = cargar_historial()
    precios_db = cargar_precios_db()
    stats = generar_estadisticas(historial, precios_db)
    enviar_telegram(stats)
    return "Estadísticas enviadas a Telegram"

def comando_configuracion(parametros=None):
    """Muestra o actualiza la configuración del bot"""
    config = cargar_configuracion()
    
    if not parametros:
        # Mostrar configuración actual
        texto = "⚙️ CONFIGURACIÓN ACTUAL DEL BOT ⚙️\n\n"
        for param, valor in config.items():
            texto += f"- {param}: {valor}\n"
        enviar_telegram(texto)
        return "Configuración enviada a Telegram"
    
    # Actualizar parámetros
    for param, valor in parametros.items():
        if param in config:
            # Convertir tipos según el parámetro
            if param in ["precio_maximo", "precio_minimo", "umbral_chollo", "tiempo_espera", "max_items_por_busqueda", "max_intentos"]:
                try:
                    config[param] = int(valor)
                except ValueError:
                    return f"Error: valor inválido para {param}"
            elif param in ["filtrar_ubicacion", "notificacion_sonido", "busqueda_inteligente"]:
                if valor.lower() in ["true", "si", "yes", "1"]:
                    config[param] = True
                elif valor.lower() in ["false", "no", "0"]:
                    config[param] = False
                else:
                    return f"Error: valor inválido para {param}"
            elif param == "ubicaciones_preferidas" and isinstance(valor, str):
                config[param] = [loc.strip() for loc in valor.split(",")]
            elif param == "modo_busqueda":
                if valor.lower() in [MODO_AVERIADOS, MODO_CHOLLOS, MODO_TODOS]:
                    config[param] = valor.lower()
                else:
                    return f"Error: modo de búsqueda inválido (valores válidos: {MODO_AVERIADOS}, {MODO_CHOLLOS}, {MODO_TODOS})"
            else:
                config[param] = valor
    
    # Guardar configuración actualizada
    guardar_configuracion(config)
    enviar_telegram("✅ Configuración actualizada correctamente")
    return "Configuración actualizada"

def comando_limpiar_historial(dias=None):
    """Limpia el historial de productos enviados"""
    historial = cargar_historial()
    
    if dias is None:
        # Eliminar todo el historial
        historial = {}
        guardar_historial(historial)
        enviar_telegram("🧹 Historial borrado completamente")
        return "Historial borrado"
    
    # Limpiar historial más antiguo que X días
    try:
        dias = int(dias)
        if dias <= 0:
            return "Error: el número de días debe ser positivo"
        
        historial = limpiar_historial_antiguo(historial, dias)
        guardar_historial(historial)
        enviar_telegram(f"🧹 Historial limpiado: se han eliminado productos más antiguos de {dias} días")
        return f"Historial limpiado (>={dias} días)"
    except ValueError:
        return "Error: formato de días inválido"

def escuchar_comandos_telegram(token, chat_id, config_file, historial_file, precios_db_file):
    """
    Escucha y procesa comandos recibidos por Telegram mediante polling.
    """
    base_url = f"https://api.telegram.org/bot{token}/"
    offset = 0

    try:
        updates = requests.get(f"{base_url}getUpdates").json()
        if updates.get("ok") and updates.get("result"):
            offset = updates["result"][-1]["update_id"] + 1
    except Exception as e:
        print(f"Error al inicializar escucha de comandos: {e}")

    config = cargar_configuracion()
    print(f"Escuchando comandos de Telegram...")

    while True:
        try:
            params = {"offset": offset, "timeout": 30}
            response = requests.get(f"{base_url}getUpdates", params=params).json()

            if response.get("ok") and response.get("result"):
                for update in response["result"]:
                    offset = update["update_id"] + 1

                    # === ✅ Procesar feedback de botones ===
                    if "callback_query" in update:
                        callback = update["callback_query"]
                        data = callback["data"]
                        user = str(callback["from"]["id"])
                        callback_id = callback["id"]

                        if user == CHAT_ID:
                            accion, id_callback = data.split("|", 1)
        
                            if accion == "like":
                                confirmar_feedback(TOKEN, callback_id, "✅ Marcado como 'Me interesa'")
                                log_actividad(f"👍 Producto marcado como 'Me interesa': {id_callback}")
                            elif accion == "dislike":
                                confirmar_feedback(TOKEN, callback_id, "❌ Marcado como 'No me interesa'")
                                log_actividad(f"👎 Producto marcado como 'No me interesa': {id_callback}")
                            elif accion == "maybe":
                                confirmar_feedback(TOKEN, callback_id, "🤔 Marcado como 'Puede interesar'")
                                log_actividad(f"🤔 Producto marcado como 'Puede interesar': {id_callback}")
                            else:
                                confirmar_feedback(TOKEN, callback_id, "❓ Acción no reconocida")
                        else:
                            confirmar_feedback(TOKEN, callback_id, "❌ Usuario no autorizado")

                    # === 💬 Procesar comandos de texto ===
                    elif "message" in update and "text" in update["message"]:
                        mensaje = update["message"]["text"]
                        user_id = str(update["message"]["from"]["id"])

                        if user_id == chat_id:
                            procesar_comando_telegram(mensaje, token, chat_id, config_file, historial_file, precios_db_file)
                        else:
                            respuesta = f"❌ Usuario no autorizado. ID: {user_id}"
                            enviar_mensaje_telegram(token, chat_id, respuesta)

            time.sleep(1)

        except Exception as e:
            print(f"Error al escuchar comandos de Telegram: {e}")
            time.sleep(10)


def procesar_comando_telegram(mensaje, token, chat_id, config_file, historial_file, precios_db_file):
    """
    Procesa los comandos recibidos por Telegram.
    """
    if mensaje == "/start" or mensaje == "/help":
        log_actividad("Comando /help recibido")
        mostrar_ayuda(token, chat_id)

    elif mensaje == "/stats" or mensaje == "/estadisticas":
        enviar_estadisticas(token, chat_id, historial_file, precios_db_file)

    elif mensaje == "/stats_completas":
        enviar_estadisticas_completas(token, chat_id, historial_file, precios_db_file)

    elif mensaje == "/config" or mensaje == "/configuracion":
        mostrar_configuracion(token, chat_id, config_file)

    elif mensaje.startswith("/set_"):
        cambiar_configuracion(mensaje, token, chat_id, config_file)

    elif mensaje == "/status":
        enviar_status(token, chat_id)

    elif mensaje == "/limpiar_historial":
        limpiar_historial_menu(token, chat_id)

    elif mensaje.startswith("/limpiar_"):
        procesar_limpieza_historial(mensaje, token, chat_id, historial_file)

    else:
        respuesta = "❓ Comando no reconocido. Usa /help para ver la lista de comandos disponibles."
        enviar_mensaje_telegram(token, chat_id, respuesta)


def mostrar_ayuda(token, chat_id):
    """Muestra la lista de comandos disponibles."""
    mensaje = (
        "🤖 *WallaBot CazaChollos - Comandos Disponibles* 🤖\n\n"
        "*Comandos básicos:*\n"
        "/start - Inicia el bot\n"
        "/help - Muestra esta ayuda\n"
        "/status - Estado del bot\n\n"
        "*Estadísticas:*\n"
        "/stats - Estadísticas básicas\n"
        "/stats_completas - Más detalles\n\n"
        "*Configuración:*\n"
        "/config - Ver configuración\n"
        "/set_precio_max [valor]\n"
        "/set_precio_min [valor]\n"
        "/set_umbral [valor]\n"
        "/set_espera [minutos]\n"
        "/set_modo [averiados|chollos|todos]\n\n"
        "*Gestión:*\n"
        "/limpiar_historial - Opciones para limpiar el historial"
    )

    enviar_mensaje_telegram(token, chat_id, mensaje, usar_markdown=True)
    
def guardar_feedback(accion, url):
    archivo = "feedback.json"
    datos = {}
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            datos = json.load(f)
    datos[url] = {"accion": accion, "timestamp": datetime.now().isoformat()}
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

def confirmar_feedback(token, callback_id, texto):
    url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
    payload = {"callback_query_id": callback_id, "text": texto}
    requests.post(url, data=payload)


def enviar_estadisticas(token, chat_id, historial_file, precios_db_file):
    """Envía estadísticas básicas al chat."""
    try:
        # Cargar datos
        historial = {}
        precios_db = {}
        
        with open(historial_file, 'r', encoding='utf-8') as f:
            historial = json.load(f)
        
        with open(precios_db_file, 'r', encoding='utf-8') as f:
            precios_db = json.load(f)
        
        # Contar por tipo
        conteo_tipos = {"averiados": 0, "chollos": 0, "desconocido": 0}
        conteo_hoy = 0
        
        hoy = datetime.now().strftime("%Y-%m-%d")
        
        for url, datos in historial.items():
            tipo = datos.get("tipo", "desconocido")
            if tipo in conteo_tipos:
                conteo_tipos[tipo] += 1
            else:
                conteo_tipos["desconocido"] += 1
            
            # Contar productos de hoy
            if "fecha" in datos and datos["fecha"].startswith(hoy):
                conteo_hoy += 1
        
        # Crear mensaje
        mensaje = (
            "📊 *Estadísticas Básicas* 📊\n\n"
            f"Total de productos: {len(historial)}\n"
            f"Productos encontrados hoy: {conteo_hoy}\n\n"
            f"*Por tipo:*\n"
            f"🔧 Averiados: {conteo_tipos['averiados']}\n"
            f"💰 Chollos: {conteo_tipos['chollos']}\n"
            f"❓ Sin clasificar: {conteo_tipos['desconocido']}\n\n"
            f"Base de datos de precios: {len(precios_db)} modelos\n\n"
            "_Para estadísticas completas usa /stats_completas_"
        )
        
        enviar_mensaje_telegram(token, chat_id, mensaje, usar_markdown=True)
        
    except Exception as e:
        mensaje = f"❌ Error al generar estadísticas: {str(e)}"
        enviar_mensaje_telegram(token, chat_id, mensaje)

def enviar_estadisticas_completas(token, chat_id, historial_file, precios_db_file):
    """Envía estadísticas detalladas al chat."""
    try:
        # Cargar datos
        historial = {}
        precios_db = {}
        
        with open(historial_file, 'r', encoding='utf-8') as f:
            historial = json.load(f)
        
        with open(precios_db_file, 'r', encoding='utf-8') as f:
            precios_db = json.load(f)
            
        # Generar estadísticas detalladas
        from collections import defaultdict
        
        # Conteo por tipo
        conteo_tipos = defaultdict(int)
        # Conteo por día
        conteo_por_dia = defaultdict(int)
        # Contar por categoría
        conteo_categorias = defaultdict(int)
        
        for url, datos in historial.items():
            tipo = datos.get("tipo", "desconocido")
            conteo_tipos[tipo] += 1
            
            # Estadísticas por día
            if "fecha" in datos:
                fecha = datos["fecha"].split("T")[0]  # Extraer solo YYYY-MM-DD
                conteo_por_dia[fecha] += 1
            
            # Contar categorías si están disponibles
            if "categoria" in datos:
                categoria = datos.get("categoria", "general")
                conteo_categorias[categoria] += 1
        
        # Ordenar días cronológicamente y obtener últimos 7
        dias_ordenados = sorted(conteo_por_dia.keys())
        dias_mostrar = dias_ordenados[-7:] if len(dias_ordenados) > 7 else dias_ordenados
        
        # Top 5 modelos con más datos
        modelos_por_datos = sorted(precios_db.items(), key=lambda x: len(x[1]["precios"]), reverse=True)[:5]
        
        # Generar mensaje (dividido en dos para no exceder límites)
        mensaje1 = (
            "📊 *Estadísticas Completas* 📊\n\n"
            f"*Total de productos registrados:* {len(historial)}\n\n"
            "*Por tipo:*\n"
        )
        
        for tipo, conteo in conteo_tipos.items():
            tipo_nombre = "Averiados" if tipo == "averiados" else "Chollos de precio"
            if tipo == "desconocido":
                tipo_nombre = "Sin clasificar"
            mensaje1 += f"- {tipo_nombre}: {conteo}\n"
        
        mensaje1 += "\n*Actividad reciente:*\n"
        
        for dia in dias_mostrar:
            mensaje1 += f"- {dia}: {conteo_por_dia[dia]} productos\n"
        
        # Enviar primera parte
        enviar_mensaje_telegram(token, chat_id, mensaje1, usar_markdown=True)
        
        # Segunda parte del mensaje
        mensaje2 = "*Continuación de estadísticas:*\n\n"
        
        if conteo_categorias:
            mensaje2 += "*Por categoría:*\n"
            for cat, count in sorted(conteo_categorias.items(), key=lambda x: x[1], reverse=True)[:8]:
                mensaje2 += f"- {cat}: {count}\n"
            mensaje2 += "\n"
        
        if precios_db:
            mensaje2 += f"*Base de datos de precios:*\n"
            mensaje2 += f"- Modelos registrados: {len(precios_db)}\n"
            
            if modelos_por_datos:
                mensaje2 += "- Top 5 modelos con más datos:\n"
                for modelo, datos in modelos_por_datos:
                    mensaje2 += f"  * {modelo}: {len(datos['precios'])} registros\n"
        
        # Enviar segunda parte
        enviar_mensaje_telegram(token, chat_id, mensaje2, usar_markdown=True)
        
    except Exception as e:
        mensaje = f"❌ Error al generar estadísticas completas: {str(e)}"
        enviar_mensaje_telegram(token, chat_id, mensaje)

def mostrar_configuracion(token, chat_id, config_file):
    """Muestra la configuración actual del bot."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        mensaje = "⚙️ *CONFIGURACIÓN ACTUAL DEL BOT* ⚙️\n\n"
        
        # Parámetros principales con formato amigable
        mensaje += "*Parámetros principales:*\n"
        mensaje += f"🔍 Modo de búsqueda: `{config['modo_busqueda']}`\n"
        mensaje += f"💰 Rango de precio: `{config['precio_minimo']}€ - {config['precio_maximo']}€`\n"
        mensaje += f"📉 Umbral para chollos: `{config['umbral_chollo']}%`\n"
        mensaje += f"⏱️ Tiempo entre búsquedas: `{config['tiempo_espera']//60} minutos`\n"
        mensaje += f"🔢 Máx. items por búsqueda: `{config['max_items_por_busqueda']}`\n\n"
        
        # Configuración adicional
        mensaje += "*Configuración adicional:*\n"
        mensaje += f"📍 Filtrar por ubicación: `{'Activado' if config['filtrar_ubicacion'] else 'Desactivado'}`\n"
        
        if config['filtrar_ubicacion']:
            ubicaciones = ", ".join(config['ubicaciones_preferidas'])
            mensaje += f"🗺️ Ubicaciones: `{ubicaciones}`\n"
        
        mensaje += f"🔊 Notificaciones con sonido: `{'Activado' if config['notificacion_sonido'] else 'Desactivado'}`\n"
        mensaje += f"🧠 Búsqueda inteligente: `{'Activado' if config['busqueda_inteligente'] else 'Desactivado'}`\n"
        mensaje += f"🔄 Reintentos en error: `{config['max_intentos']}`\n"
        mensaje += f"📅 Días para historial: `{config['enviados_max_dias']}`\n\n"
        
        mensaje += "*Para cambiar la configuración usa:*\n"
        mensaje += "`/set_precio_max [valor]` - Precio máximo\n"
        mensaje += "`/set_precio_min [valor]` - Precio mínimo\n"
        mensaje += "`/set_umbral [valor]` - Umbral de chollo\n"
        mensaje += "`/set_espera [valor]` - Tiempo entre búsquedas (min)\n"
        mensaje += "`/set_modo [modo]` - Modo: averiados, chollos o todos\n"
        
        enviar_mensaje_telegram(token, chat_id, mensaje, usar_markdown=True)
        
    except Exception as e:
        mensaje = f"❌ Error al mostrar configuración: {str(e)}"
        enviar_mensaje_telegram(token, chat_id, mensaje)

def cambiar_configuracion(mensaje, token, chat_id, config_file):
    """
    Cambia la configuración del bot según el comando recibido.
    
    Formato:
    /set_parametro valor
    """
    try:
        # Extraer comando y valor
        partes = mensaje.split()
        if len(partes) < 2:
            enviar_mensaje_telegram(token, chat_id, "❌ Formato incorrecto. Usa /set_parametro valor")
            return
            
        comando = partes[0]
        valor = partes[1]
        
        # Cargar configuración actual
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # Procesar según comando
        if comando == "/set_precio_max":
            try:
                precio_max = int(valor)
                if precio_max <= config["precio_minimo"]:
                    enviar_mensaje_telegram(token, chat_id, "❌ El precio máximo debe ser mayor que el mínimo.")
                    return
                config["precio_maximo"] = precio_max
                mensaje_ok = f"✅ Precio máximo establecido a {precio_max}€"
            except ValueError:
                enviar_mensaje_telegram(token, chat_id, "❌ El valor debe ser un número entero.")
                return
                
        elif comando == "/set_precio_min":
            try:
                precio_min = int(valor)
                if precio_min <= 0:
                    enviar_mensaje_telegram(token, chat_id, "❌ El precio mínimo debe ser mayor que 0.")
                    return
                if precio_min >= config["precio_maximo"]:
                    enviar_mensaje_telegram(token, chat_id, "❌ El precio mínimo debe ser menor que el máximo.")
                    return
                config["precio_minimo"] = precio_min
                mensaje_ok = f"✅ Precio mínimo establecido a {precio_min}€"
            except ValueError:
                enviar_mensaje_telegram(token, chat_id, "❌ El valor debe ser un número entero.")
                return
                
        elif comando == "/set_umbral":
            try:
                umbral = int(valor)
                if umbral < 0 or umbral > 95:
                    enviar_mensaje_telegram(token, chat_id, "❌ El umbral debe estar entre 0 y 95%.")
                    return
                config["umbral_chollo"] = umbral
                mensaje_ok = f"✅ Umbral de chollo establecido a {umbral}%"
            except ValueError:
                enviar_mensaje_telegram(token, chat_id, "❌ El valor debe ser un número entero.")
                return
                
        elif comando == "/set_espera":
            try:
                minutos = int(valor)
                if minutos < 1:
                    enviar_mensaje_telegram(token, chat_id, "❌ El tiempo de espera debe ser al menos 1 minuto.")
                    return
                config["tiempo_espera"] = minutos * 60  # Convertir a segundos
                mensaje_ok = f"✅ Tiempo entre búsquedas establecido a {minutos} minutos"
            except ValueError:
                enviar_mensaje_telegram(token, chat_id, "❌ El valor debe ser un número entero.")
                return
                
        elif comando == "/set_modo":
            modo = valor.lower()
            if modo not in ["averiados", "chollos", "todos"]:
                enviar_mensaje_telegram(token, chat_id, "❌ Modo no válido. Opciones: averiados, chollos, todos")
                return
            config["modo_busqueda"] = modo
            mensaje_ok = f"✅ Modo de búsqueda establecido a '{modo}'"
                
        else:
            enviar_mensaje_telegram(token, chat_id, "❌ Comando de configuración no reconocido.")
            return
            
        # Guardar configuración actualizada
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
            
        # Enviar confirmación
        enviar_mensaje_telegram(token, chat_id, mensaje_ok)
        
    except Exception as e:
        mensaje = f"❌ Error al cambiar configuración: {str(e)}"
        enviar_mensaje_telegram(token, chat_id, mensaje)

def enviar_status(token, chat_id):
    """Muestra el estado actual del bot."""
    # Obtener timestamp actual
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    mensaje = (
        "🤖 *Estado del WallaBot* 🤖\n\n"
        f"⏱️ Hora actual: {ahora}\n"
        "✅ Bot en funcionamiento\n\n"
        "*Comandos disponibles:*\n"
        "/config - Ver configuración actual\n"
        "/stats - Ver estadísticas básicas\n"
        "/help - Ver todos los comandos\n"
    )
    
    enviar_mensaje_telegram(token, chat_id, mensaje, usar_markdown=True)

def limpiar_historial_menu(token, chat_id):
    """Muestra el menú para limpiar historial."""
    mensaje = (
        "🧹 *Opciones para limpiar historial* 🧹\n\n"
        "/limpiar_todo - Eliminar todo el historial\n"
        "/limpiar_7 - Eliminar entradas más antiguas de 7 días\n"
        "/limpiar_15 - Eliminar entradas más antiguas de 15 días\n"
        "/limpiar_30 - Eliminar entradas más antiguas de 30 días\n"
    )
    
    enviar_mensaje_telegram(token, chat_id, mensaje, usar_markdown=True)

def procesar_limpieza_historial(mensaje, token, chat_id, historial_file):
    """Procesa la limpieza del historial según el comando recibido."""
    try:
        # Cargar historial actual
        with open(historial_file, 'r', encoding='utf-8') as f:
            historial = json.load(f)
            
        historial_original = len(historial)
        
        if mensaje == "/limpiar_todo":
            # Eliminar todo
            historial = {}
            mensaje_ok = f"✅ Historial borrado completamente. Se eliminaron {historial_original} registros."
            
        elif mensaje in ["/limpiar_7", "/limpiar_15", "/limpiar_30"]:
            # Extraer número de días
            dias = int(mensaje.split("_")[1])
            
            # Limpiar historial antiguo
            from datetime import datetime, timedelta
            limite = (datetime.now() - timedelta(days=dias)).isoformat()
            nuevo_historial = {}
            
            for url, datos in historial.items():
                if "fecha" in datos and datos["fecha"] >= limite:
                    nuevo_historial[url] = datos
            
            historial = nuevo_historial
            eliminados = historial_original - len(historial)
            mensaje_ok = f"✅ Se eliminaron {eliminados} registros más antiguos de {dias} días."
            
        else:
            enviar_mensaje_telegram(token, chat_id, "❌ Comando de limpieza no reconocido.")
            return
            
        # Guardar historial actualizado
        with open(historial_file, 'w', encoding='utf-8') as f:
            json.dump(historial, f, ensure_ascii=False, indent=4)
            
        # Enviar confirmación
        enviar_mensaje_telegram(token, chat_id, mensaje_ok)
        
    except Exception as e:
        mensaje = f"❌ Error al limpiar historial: {str(e)}"
        enviar_mensaje_telegram(token, chat_id, mensaje)

def enviar_mensaje_telegram(token, chat_id, mensaje, usar_markdown=False):
    """Envía un mensaje a través de Telegram."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': mensaje
    }
    
    if usar_markdown:
        payload['parse_mode'] = 'Markdown'
        
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Error al enviar mensaje a Telegram: {e}")

# --- Integración con el código principal ---

def iniciar_escucha_telegram(token, chat_id, config_file, historial_file, precios_db_file):
    """
    Inicia un hilo separado para escuchar comandos de Telegram.
    
    Esta función debe llamarse desde main() para iniciar la escucha en segundo plano.
    """
    # Crear y comenzar el hilo
    telegram_thread = threading.Thread(
        target=escuchar_comandos_telegram,
        args=(token, chat_id, config_file, historial_file, precios_db_file),
        daemon=True  # El hilo se cerrará cuando el programa principal termine
    )
    
    telegram_thread.start()
    return telegram_thread
      
def main():
    
    def manejador_señal(sig, frame):
        log_actividad("📴 Señal de interrupción recibida. Cerrando bot.")
        sys.exit(0)

    # Registrar manejador de señales para salida limpia
    signal.signal(signal.SIGINT, manejador_señal)
    signal.signal(signal.SIGTERM, manejador_señal)
    
    # Cargar configuración
    config = cargar_configuracion()
    
    # Mensaje de inicio
    log_actividad("🚀 WallaBot CazaChollos iniciado")
    mensaje_inicio = (
        "🤖 *WallaBot CazaChollos Iniciado* 🤖\n\n"
        f"Configurado para detectar productos {config['modo_busqueda']} "
        f"entre {config['precio_minimo']}€ y {config['precio_maximo']}€\n\n"
        "Envía /help para ver los comandos disponibles."
    )
    enviar_telegram(mensaje_inicio, usar_markdown=True)
    
    # Iniciar escucha de comandos de Telegram en segundo plano
    telegram_thread = iniciar_escucha_telegram(
        TOKEN, 
        CHAT_ID, 
        CONFIG_FILE,
        HISTORIAL_FILE,
        PRECIOS_DB_FILE
    )
    
    intentos_fallidos = 0
    max_intentos = config["max_intentos"]
    
    while True:
        try:
            # Recargar configuración en cada iteración para detectar cambios
            config = cargar_configuracion()
            
            nuevos = buscar_wallapop(config)
            log_actividad(f"👍 Búsqueda completada: {nuevos} productos nuevos encontrados")
            intentos_fallidos = 0  # Resetear contador si la búsqueda tuvo éxito
            
            # Esperar para la próxima búsqueda
            espera = config["tiempo_espera"]
            log_actividad(f"🕒 Esperando {espera//60} minutos para la próxima búsqueda...\n")
            time.sleep(espera)
            
        except Exception as e:
            intentos_fallidos += 1
            log_actividad(f"❌ Error en el ciclo principal: {str(e)}")
            
            if intentos_fallidos >= max_intentos:
                log_actividad("⚠️ Demasiados errores consecutivos. Pausando durante 30 minutos...")
                enviar_telegram("⚠️ El bot ha encontrado problemas y está en pausa temporal. Volveré en 30 minutos.")
                time.sleep(1800)  # Pausa más larga tras múltiples fallos
                intentos_fallidos = 0
            else:
                log_actividad(f"⚠️ Reintentando en 5 minutos... (intento {intentos_fallidos}/{max_intentos})")
                time.sleep(300)
                
if __name__ == "__main__":
	main()

