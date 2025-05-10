import socket
import threading
import os
from datetime import datetime

### Funciones auxiliares ###
#se limpia la consola
def limpiar_consola():
    os.system("cls" if os.name == "nt" else "clear")

#se crea un separador para separar mensajes
def imprimir_separador():
    print("\n" + "=" * 50 + "\n")

#se escribe en el log file
def loggear(texto, tipo="INFO"):
    with open("log_cliente.txt", "a", encoding="utf-8") as log:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.write(f"[{timestamp}] [{tipo}] {texto}\n")

#espera un numero de input
def espera_numero(mensaje):
    return "Ingrese un número" in mensaje or mensaje.strip().endswith("número:")

#espera un mensaje
def recibir_msg(socket):
    while True:
        msg = socket.recv(1024).decode().strip()
        if msg:
            print(f"\n{msg}")
        break

#se definen variables
HOST = "127.0.0.1"
PORT = 5555

cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((HOST, PORT))

print("Conectado al servidor.")
loggear("Conectado al servidor.", "INFO")

try:
    while True:
        msg_server = cliente.recv(4096).decode().strip() #se recibe mensaje del servidor
        #Se busca guardar el nombre del cliente para el caso de un chat
        if "Bienvenido" in msg_server:
            partes = msg_server.split("¡Bienvenido")
            if len(partes) > 1:
                nombre_raw = partes[1].split("!")[0].strip() #se separa el nombre del cliente
                nombre_cl = nombre_raw  #Se guarda el nombre del cliente

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

        if msg_server.endswith(":") or msg_server.endswith("número:") or msg_server.endswith("otra vez:") or msg_server.endswith("desea:"):
            while True:
                msg_cliente = input(">> ").strip()

                if not msg_cliente:
                    print("⚠️ No puede dejar el campo vacío. Intente de nuevo.")
                    continue

                if espera_numero(msg_server):
                    if not msg_cliente.isdigit():
                        print("❌ Ingrese solo un número válido para el menú.")
                        continue

                if "contraseña" in msg_server.lower():
                    loggear("Se ingresó una contraseña (oculta por seguridad).", "CLIENTE")
                else:
                    loggear(msg_cliente, "CLIENTE")

                cliente.send(msg_cliente.encode())
                break

        #se activa el modo chat
        if "Conectado con un ejecutivo" in msg_server: #se detecta que se inicia el chat con un ejecutivo
            print("\n ----- Chat iniciado ----- \nEscriba 'salir para terminar el chat.' \n")
            hilo_receptor = threading.Thread(target=recibir_msg, args=(cliente,), daemon=True) #para recibir y enviar mensajes por turnos (se buguea y frena)
            hilo_receptor.start()

            while True:
                msg_cliente = input(f"{nombre_cl}: ").strip() #mensaje del cliente

                if not msg_cliente: #detector de mensaje en vacio (yo creo que se puede eliminar)
                    print("⚠️ No puede dejar el campo vacío. Intente de nuevo.")
                    continue

                cliente.send(msg_cliente.encode()) #se envia mensaje del cliente
                if msg_cliente.lower() == "salir": #detecta si el cliente cierra el chat
                    break

                #respuesta del ejecutivo
                res_ejecutivo = cliente.recv(1024).decode().strip() 
                if res_ejecutivo:
                    print(res_ejecutivo)
            continue #creo que este es el culpable de que frenen los mensajes, al menos respecto al cliente
        #### Quizas hay que hacer que el cliente primero reciba mensaje de ejecutivo y luego envia mensaje sino se buguea ####

#detectores de errores y cierres de la sesion
except Exception as e:
    loggear(f"Error: {e}", "ERROR")
    print(f"[ERROR] {e}")

finally:
    cliente.close()
    print("Te has desconectado.")
    loggear("Cliente desconectado.", "INFO")