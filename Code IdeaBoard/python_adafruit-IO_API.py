import gc
gc.collect()

from ideaboard import IdeaBoard
ib = IdeaBoard()
ib.pixe = (0, 0, 0)

from ideasense import IdeaSense
idea = IdeaSense()

import socketpool
import digitalio
import ssl
import wifi
import adafruit_requests as requests
import time
import os
import board


gc.collect()

# Inicializar IdeaBoard e IdeaSense #

ib.pixe = (0, 0, 0)

# CREDENCIALES DE ADAFRUIT IO #
AIO_USERNAME = "AIO_USERNAME"
AIO_KEY = "AIO_KEY"
FEED_NAME_LIGHT = "Light"
FEED_NAME_TEMP = "Temperature"
FEED_NAME_HUMID = "Humidity"
FEED_NAME_RAM = "RAM"

# ADAFRUIT IO URLS PARA CADA FEED DE SENSORES # 
AIO_URL_LIGHT = f"http://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/light/data"
AIO_URL_TEMP = f"http://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/temperature/data"
AIO_URL_HUMID = f"http://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/humedad/data"
AIO_URL_RAM = f"http://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/ram/data"

# Configurar encabezados HTTP para autenticación y tipo de contenido #
headers = {
    "X-AIO-Key": AIO_KEY,
    "Content-Type": "application/json",
    "Connection": "close"
}

# CONFIGURAR PINES DE SALIDA PARA BOMBA DE AGUA Y LED INDICADOR # 
pump = digitalio.DigitalInOut(board.IO18)
pump.direction = digitalio.Direction.OUTPUT
pump.value = False 

# CONFIGURAR LOG PARA CSV #

CSV_FILE = "/sensor_data_log.csv"

def log_data_to_csv(light_level, temp_level, humid_level, ram_space):
    try: 
        # Verificar si el archivo CSV existe, si no, crear uno nuevo con encabezados
        file_exists = "sensor_data_log.csv" in os.listdir("/") 
        
        if not file_exists:
            with open(CSV_FILE, "w") as f:
                f.write("Light Level,Temperature Level,Humidity Level,RAM Space\n")

        # Agregar los datos de los sensores al archivo CSV
        with open(CSV_FILE, "a") as f:
            f.write(f"{light_level},{temp_level},{humid_level},{ram_space}\n")

    except OSError as e:
        print(f"Error writing to CSV file:", repr(e)) 
        

# DEFINIR FUNCIONES DE SENSORES #

def medir_sensores():
    light_level = idea.light   
    temp_level = idea.temp
    humid_level = idea.humid
    ram_space = gc.mem_free()
    return light_level, temp_level, humid_level, ram_space

# DEFINIR FUNCION PARA MOSTRAR ESTADO DE LA TARJETA DE RED (NIC) #
def nic_status():
    
    # Mostrar direccion IP
    IP_add = wifi.radio.ipv4_address
    MAC_add = wifi.radio.mac_address
    return IP_add, MAC_add

# DEFINIR FUNCION PARA CONTROLAR BOMBA DE AGUA Y LED INDICADOR #

def check_agua_bomba(light_level, humid_level, pump_pin):
    if light_level < 10 and humid_level < 90:
        print("Condición cumplida: Bomba ENCENDIDA.")
        ib.pixel = (150,0,0)
        pump_pin.value = True
        time.sleep(5.0)
        pump_pin.value = False
        print("Bomba de agua APAGADA despues de 5 segundos")
    else:
        ib.pixel = (0, 155, 0)
        print("Condicion no cumplida: Bomba APAGADA")
    return None

# SOCKET POOL Y SESION HTTP
socket = socketpool.SocketPool(wifi.radio)
https = requests.Session(socket, None)

# CONECTAR A WIFI #
print("Connecting to WiFi...")
wifi.radio.connect("ssid", "password")
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

ciclo = 0

# Abrir loop para enviar valores POST de sensores 
while True:

    # Forzar garbage collection para prevenir fragmentacion y fugas
    gc.collect()
    
    ciclo += 1 
    # Invocar valores de sensores
    light_level, temp_level, humid_level, ram_space = medir_sensores()
    IP_add, MAC_add = nic_status()

    # Preparar payload JSON enviado por Adafruit IO
    payload_light = {"value": light_level}
    payload_temp = {"value": temp_level}
    payload_humid = {"value": humid_level}
    payload_ram = {"value": ram_space}

    
    # GUARDAR DATOS EN ARCHIVO CSV LOCAL
    light_level, temp_level, humid_level, ram_space = medir_sensores()

    # LLAMAR FUNCION DE LA BOMBA DE AGUA Y LED #
    check_agua_bomba(light_level, humid_level, pump)

    # Guardar datos en archivo CSV #
    bomba_activa = (light_level < 30 and humid_level < 50)
    log_data_to_csv(light_level, temp_level, humid_level, ram_space) 
    
    
    
    try:
        # INVOCAR FUNCION PARA MOSTRAR VALORES DE SENSORES EN CONSOLA #
        # Enviar data por solicitud HTTP POST luz
        response_light = https.post(AIO_URL_LIGHT, json=payload_light, headers=headers)
        print(f"Light Response:{response_light.status_code}")
        if response_light.status_code != 200:
            print(f"Error detail: {response_light.text}")
            
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

        # Pausa entre llamadas
        time.sleep(0.5)

        # Enviar data por solicitud HTTP POST RAM
        response_ram = https.post(AIO_URL_RAM, json=payload_ram, headers=headers)
        print(f"Available RAM Response:{response_ram.status_code}")
        response_ram.close()
        del response_ram
    
        Consola()
        check_agua_bomba(light_level, humid_level, pump)



    # Mostrar error 
    except Exception as e:
        print("Failed to send data:", repr(e)) 
        time.sleep(0.5)

    # Adafruit IO delimitador de tiempo: max 1 solicitud cada 15 segundos    
    gc.collect()
    time.sleep(15.0)
