import socketpool
import digitalio
import ssl
import wifi
import adafruit_requests as requests
import time
import gc
import board
from ideasense import IdeaSense
from ideaboard import IdeaBoard

ib = IdeaBoard()
idea = IdeaSense()

# Credenciales para Adafruit IO
AIO_USERNAME = "AIO_USERNAME"
AIO_KEY = "AIO_KEY"
FEED_NAME_LIGHT = "Light"
FEED_NAME_TEMP = "Temperature"
FEED_NAME_HUMID = "Humidity"
FEED_NAME_RAM = "RAM"

# Adafruit IO HTTP REST endpoint URL
AIO_URL_LIGHT = f"http://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/light/data"
AIO_URL_TEMP = f"http://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/temperature/data"
AIO_URL_HUMID = f"http://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/humedad/data"
AIO_URL_RAM = f"http://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/ram/data"

# Headers required for authentication and content type
headers = {
    "X-AIO-Key": "AIO_KEY",
    "Content-Type": "application/json",
    "Connection": "close"
}

# Configurar pin conectado a la bomgba
pump = digitalio.DigitalInOut(board.IO18)
pump.direction = digitalio.Direction.OUTPUT
pump.value = False 

# Definir funcion de medir sensores 
def medir_sensores():
     # Medir Luz 
    light_level = idea.light   
    # Medir Temperatura 
    temp_level = idea.temp
    # Medir Humedad
    humid_level = idea.humid
    # RAM space
    ram_space = gc.mem_free() 

    return light_level, temp_level, humid_level, ram_space

# Funcion para definir mostrar configuracion NIC
def nic_status():
    
    # Mostrar direccion IP
    IP_add = wifi.radio.ipv4_address
    MAC_add = wifi.radio.mac_address

    return IP_add, MAC_add

def check_agua_bomba(light_level, humid_level, pump_pin):
    if light_level < 30 and humid_level < 90:
        print("Condición cumplida: Bomba ENCENDIDA.")
        ib.pixel = (150,0,0)
        pump_pin.value = True
        time.sleep(5.0)
        pump_pin.value = False
        print("Bomba de agua APAGADA despues de 5 segundos")
    else:
        ib.pixel = (0, 155, 0)
        print("Condicion no cumplida: Bomba APAGADA")
    return check_agua_bomba

# Socket pool actuando como administrador de canales de comunicacion disponibles
socket = socketpool.SocketPool(wifi.radio)

# Tomar el socket pool creado por en socket para saber como enviar y recibir data por la red
https = requests.Session(socket, None)

# Conectar WiFi
print("Connecting to WiFi...")
wifi.radio.connect("SSID", "password")
print("Connected to Wifi!")

# Funcion para mostrar valores de sensores en consola

def Consola():
    print("*********** MENSAJE ENTRANTE ***********")
    print(f"Light level is: {idea.light}")
    print(f"Temp level is: {idea.temp}")
    print(f"Humid level is: {idea.humid}")
    print(f"Free RAM: {gc.mem_free()} bytes")
    print(f"My IP address: {wifi.radio.ipv4_address}")
    print(f"My MAC address: {wifi.radio.mac_address}")
    print("*********** FIN DEL MENSAJE ***********")

# Abrir loop para enviar valores POST de sensores 
while True:

    # Forzar garbage collection para prevenir fragmentacion y fugas
    gc.collect()
    
    # Invocar valores de sensores
    light_level, temp_level, humid_level, ram_space = medir_sensores()
    IP_add, MAC_add = nic_status()

    # Preparar payload JSON enviado por Adafruit IO
    payload_light = {"value": light_level}
    payload_temp = {"value": temp_level}
    payload_humid = {"value": humid_level}
    payload_ram = {"value": ram_space}

    
    # Llamar funcion de la bomba y LED #
    check_agua_bomba(light_level, humid_level, pump)


    try:
        
        # Invocar funcion de consola 
        Consola()
        # Enviar data por solicitud HTTP POST luz
        response_light = https.post(AIO_URL_LIGHT, json=payload_light, headers=headers)
        print(f"Light Response:{response_light.status_code}")
        response_light.close()
        del response_light

        #Pausa entre llamadas
        time.sleep(0.5)

        # Enviar data por solicitud HTTP POST temp
        response_temp = https.post(AIO_URL_TEMP, json=payload_temp, headers=headers)
        print(f"Temp Response:{response_temp.status_code}")
        response_temp.close()
        del response_temp

        # Pausa entre llamadas
        time.sleep(0.5)

        # Enviar data por solicitud HTTP POST humid
        response_humid = https.post(AIO_URL_HUMID, json=payload_humid, headers=headers)
        print(f"Humidity Response:{response_humid.status_code}")
        response_humid.close()
        del response_humid

        # Paussa entre llamadas
        time.sleep(0.5)

        # Enviar data por solicitud HTTP POST RAM
        response_ram = https.post(AIO_URL_RAM, json=payload_ram, headers=headers)
        print(f"Available RAM Response:{response_ram.status_code}")
        response_ram.close()
        del response_ram
    
    # Mostrar error 
    except Exception as e:
        print("Failed to send data:", repr(e)) 
        time.sleep(0.5)

    # Adafruit IO delimitador de tiempo: max 1 solicitud cada 15 segundos    
    gc.collect()
    time.sleep(15.0)

