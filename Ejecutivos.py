import socket
import os
from datetime import datetime

def limpiar_consola():
    os.system("cls" if os.name == "nt" else "clear")

def imprimir_separador():
    print("\n" + "=" * 50 + "\n")

def loggear(texto, tipo="INFO"):
    with open("log_admin.txt", "a", encoding="utf-8") as log:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.write(f"[{timestamp}] [{tipo}] {texto}\n")

def espera_numero(mensaje):
    return "Ingrese un número" in mensaje or mensaje.strip().endswith("número:")

HOST = "127.0.0.1"
PORT = 5555

ejecutivo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ejecutivo.connect((HOST, PORT))
print("Conectado al servidor.")
loggear("Conectado al servidor.", "INFO")

try:
    while True:
        msg_server = ejecutivo.recv(4096).decode().strip()
        loggear(msg_server, "SERVIDOR")

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

except Exception as e:
    loggear(f"Error: {e}", "ERROR")
    print(f"[ERROR] {e}")

finally:
    ejecutivo.close()
    print("Te has desconectado.")
    loggear("Ejecutivo desconectado.", "INFO")
