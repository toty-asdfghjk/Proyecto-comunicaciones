import socket
import threading
import os
from datetime import datetime
import sys
import time

### Funciones auxiliares ###
#se limpia la consola
def limpiar_consola():
    os.system("cls" if os.name == "nt" else "clear")

#se crea un separador para separar mensajes
def imprimir_separador():
    print("\n" + "=" * 50 + "\n")

#se escribe en el log file
def loggear(texto, tipo="INFO"):
    with open("log_admin.txt", "a", encoding="utf-8") as log:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.write(f"[{timestamp}] [{tipo}] {texto}\n")

#espera un numero de input
def espera_numero(mensaje):
    return "Ingrese un número" in mensaje or mensaje.strip().endswith("número:")

#espera un mensaje
def recibir_msg_chat(socket, nombre):
    while True:
        try:
            msg = socket.recv(1024).decode().strip()
            if not msg:
                break
            if msg.lower() == "salir":
                break

            sys.stdout.write("\r" + " " * 100 + "\r")  # Limpia línea
            print(msg)
            sys.stdout.write(f"{nombre}: ")
            sys.stdout.flush()
            time.sleep(0.1)
        except:
            print(f"[ERROR] {e}")
            break
        

#se definen variables

        
HOST = "127.0.0.1"
PORT = 5555

ejecutivo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ejecutivo.connect((HOST, PORT))



print("Conectado al servidor.")
loggear("Conectado al servidor.", "INFO")

try:
    while True:
        msg_server = ejecutivo.recv(4096).decode().strip() #se recibe mensaje del servidor
        #Se busca guardar el nombre del ejecutivo para el caso de un chat
        if "Asistente: Hola" in msg_server:
            partes = msg_server.split("Asistente: Hola")
            if len(partes) > 1:
                nombre_raw = partes[1].split(".")[0].strip() #se separa el nombre del ejecutivo
                nombre_ej = nombre_raw  #Se guarda el nombre del ejecutivo

        loggear(msg_server, "SERVIDOR") #se escribe en el log file

        imprimir_separador()

        if "Historial" in msg_server or "Compras" in msg_server:
            for i, linea in enumerate(msg_server.splitlines(), 1):
                print(f"{linea}")
        elif "Catálogo" in msg_server or "Productos disponibles" in msg_server:
            print("[CATÁLOGO DE PRODUCTOS]\n")
            print(msg_server)
        elif "Bienvenido" in msg_server or "Asistente" in msg_server:
            limpiar_consola()
            print(f"{msg_server}\n")
        elif msg_server.startswith("[") and "Ingrese un número" in msg_server:
            print("[MENÚ PRINCIPAL]")
            print(msg_server)
        else:
            print(msg_server)


        if "Desconectando" in msg_server or "Gracias por usar" in msg_server:
            break
        
        if msg_server.endswith(":") or msg_server.endswith("\n") or msg_server == "\u200A":
            while True:
                msg_ejecutivo = input(">> ").strip()

                if not msg_ejecutivo:
                    print("⚠️ No puede dejar el campo vacío. Intente de nuevo.")
                    continue

                if espera_numero(msg_server):
                    if not msg_ejecutivo.isdigit():
                        print("❌ Ingrese solo un comando válido.")
                        continue

                if "contraseña" in msg_server.lower():
                    loggear("Se ingresó una contraseña (oculta por seguridad).", "EJECUTIVO")
                else:
                    loggear(msg_ejecutivo, "EJECUTIVO")

                ejecutivo.send(msg_ejecutivo.encode())
                break

        #se activa el modo chat
        if "Conectado con un cliente" in msg_server: #se detecta que se inicia el chat con un cliente
            print("\n ----- Chat iniciado ----- \nEscriba ':disconnect' para terminar el chat. \n")
            hilo_receptor = threading.Thread(target=recibir_msg_chat, args=(ejecutivo, nombre_ej), daemon=True)
            hilo_receptor.start()

            while True:
                try:
                    msg_ejecutivo = input(f"{nombre_ej}: ")
                    
                    if not msg_ejecutivo: #detector de mensaje en vacio (yo creo que se puede eliminar)
                        continue

                    ejecutivo.send(f"{msg_ejecutivo}".encode()) #se envia mensaje del ejecutivo
                    if msg_ejecutivo.lower() == ":disconnect":
                        break
                except Exception as e:
                    print(f"[ERROR] {e}")
                    break


#detectores de errores y cierres de la sesion
except Exception as e:
    loggear(f"Error: {e}", "ERROR")
    print(f"[ERROR] {e}")

finally:
    ejecutivo.close()
    print("Te has desconectado.")
    loggear("Ejecutivo desconectado.", "INFO")
