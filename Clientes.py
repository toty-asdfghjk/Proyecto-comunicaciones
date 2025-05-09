import socket
import os

# Limpieza de consola según el sistema operativo
def limpiar_consola():
    os.system("cls" if os.name == "nt" else "clear")

# Mostrar un separador
def imprimir_separador():
    print("\n" + "=" * 50 +"\n")

# Detecta si el servidor está esperando un número como opción
def espera_numero(mensaje):
    return "Ingrese un número" in mensaje or mensaje.strip().endswith("número:")


HOST = "127.0.0.1"
PORT = 5555

cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((HOST, PORT))
print("Conectado al servidor.")

try:
    while True:
        # Recibir mensaje del servidor
        msg_server = cliente.recv(4096).decode().strip()

        # Mostrar mensaje con formato
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

        # Si es una despedida o desconexión, salir
        if "Desconectando" in msg_server or "Gracias por usar" in msg_server:
            break

        # Solo pedir entrada si hay una pregunta esperándola
        if msg_server.endswith(":") or msg_server.endswith("número:") or msg_server.endswith("otra vez:") or msg_server.endswith("desea:"):
            while True:
                msg_cliente = input(">> ").strip()
                
                # No permitir vacío
                if not msg_cliente:
                    print("⚠️ No puede dejar el campo vacío. Intente de nuevo.")
                    continue

                # Validación de número si es menú
                if espera_numero(msg_server):
                    if not msg_cliente.isdigit():
                        print("❌ Ingrese solo un número válido para el menú.")
                        continue

                cliente.send(msg_cliente.encode())
                break  # Input válido, salir del bucle
except Exception as e:
    print(f"[ERROR] {e}")

finally:
    cliente.close()
    print("Te has desconectado.")
