import socket

# Se asume que el servidor esta corriendo localmente en el puerto 8889.
HOST = "127.0.0.1"
PORT = 5555

cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((HOST, PORT))
print("Conectado al servidor.")

try:
    while True:
        msg_server = cliente.recv(1024).decode()
        if msg_server == "Credenciales erroneas. Desconectando...":
            print(f"[SERVIDOR]: {msg_server}")
            cliente.close()
            print("Te has desconectado.")
            break
        else: print(f"[SERVIDOR]: {msg_server}")

        msg_cliente = input(">> ")
        cliente.send(msg_cliente.encode())

        if msg_cliente.strip() == "salir":
            break

except:
    cliente.close()
    print("Te has desconectado.")