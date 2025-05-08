import socket
import threading
import json
from datetime import datetime

# Configuración del servidor
HOST = "127.0.0.1"
PORT = 5555

# Carga de la base de datos
with open("Data Base.json", "r") as bases:
    dataBase = json.load(bases)

# Guardar base de datos después de cambios
def guardar_base():
    with open("Data Base.json", "w") as archivo:
        json.dump(dataBase, archivo, indent=4)

# Función principal del servidor
def revivan_el_server():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((HOST, PORT))
    servidor.listen(15)
    print("[SERVIDOR] Esperando conexiones...")

    while True:
        conexion, direccion = servidor.accept()
        thread = threading.Thread(target=clientesConect, args=(conexion, direccion))
        thread.start()
        print(f"[SERVIDOR] Conexiones activas: {threading.active_count() - 1}")

# Manejo de cliente
def clientesConect(conexion, direccion):
    print(f"[NUEVA CONEXIÓN] {direccion} conectado.")

    try:
        conexion.send(("¡Bienvenido a la plataforma de servicio al cliente de la tienda TC5G! \n"
                       "Para autenticarse ingrese su mail y contraseña: \n"
                       "\nIngrese su correo: ").encode())
        correo = conexion.recv(1024).decode().strip()
        conexion.send("Ingrese su contraseña: ".encode())
        password = conexion.recv(1024).decode().strip()

        typeUser = None
        nombre = None

        if correo in dataBase["clientes"]:
            if dataBase["clientes"][correo]["pass"] == password:
                typeUser = "cliente"
                nombre = dataBase["clientes"][correo]["nombre"]

        elif correo in dataBase["ejecutivos"]:
            if dataBase["ejecutivos"][correo]["pass"] == password:
                typeUser = "ejecutivo"
                nombre = dataBase["ejecutivos"][correo]["nombre"]

        if typeUser == "cliente":
            conexion.send(f"Asistente: ¡Bienvenido {nombre}! ¿En qué te podemos ayudar?\n".encode())
            while True:
                menu = (
                    "[1] Cambio de contraseña.\n"
                    "[2] Historial de operaciones.\n"
                    "[3] Catálogo de productos / Comprar productos.\n"
                    "[4] Solicitar devolución.\n"
                    "[5] Confirmar envío.\n"
                    "[6] Contactarse con un ejecutivo.\n"
                    "[7] Salir\n"
                    "Ingrese un número:\n")
                conexion.send(menu.encode())
                opcion = conexion.recv(1024).decode().strip()

                if opcion == "1":
                    conexion.send("Ingrese nueva contraseña: ".encode())
                    newPassword = conexion.recv(1024).decode().strip()
                    conexion.send("Ingrese su nueva contraseña otra vez: ".encode())
                    newPassword2 = conexion.recv(1024).decode().strip()
                    if newPassword == newPassword2:
                        dataBase["clientes"][correo]["pass"] = newPassword
                        guardar_base()
                        conexion.send("Contraseña actualizada exitosamente.\n".encode())
                    else:
                        conexion.send("Las contraseñas no coinciden. Se le regresará al menú.\n".encode())

                elif opcion == "2":
                    historial = dataBase["clientes"][correo].get("compras", [])
                    if not historial:
                        conexion.send("No hay operaciones registradas.\n".encode())
                    else:
                        compras = "\n".join(historial)
                        conexion.send(f"Compras:\n{compras}\n".encode())

                elif opcion == "3":
                    productos = dataBase.get("productos", {})
                    if not productos:
                        conexion.send("No hay productos disponibles en este momento.\n".encode())
                    else:
                        lista = "\n".join(
                            [f"prodID: {prodID} - {info['nombre']} (${info['precio']})" for prodID, info in productos.items()]
                        )
                        conexion.send(f"Productos disponibles:\n{lista}\nSeleccione ID del producto que desea:\n".encode())
                        prodID = conexion.recv(1024).decode().strip()
                        if prodID in productos:
                            fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
                            producto = productos[prodID]["nombre"]
                            registro = f"{producto} ({fecha})"
                            dataBase["clientes"][correo].setdefault("compras", []).append(registro)
                            guardar_base()
                            conexion.send("Compra registrada exitosamente.\n".encode())
                        else:
                            conexion.send("ID inválido.\n".encode())

                elif opcion == "4":
                    conexion.send("Ingrese ID del producto a devolver:\n".encode())
                    prodID = conexion.recv(1024).decode().strip()
                    conexion.send("Motivo de la devolución:\n".encode())
                    motivo = conexion.recv(1024).decode().strip()
                    conexion.send("Solicitud de devolución registrada. Lamentamos los inconvenientes 😔.\n".encode())

                elif opcion == "5":
                    conexion.send("Confirmación de envío recibida. ¡Gracias por comprar con nosotros!\n".encode())

                elif opcion == "6":
                    conexion.send("Un ejecutivo se comunicará contigo pronto. Por favor ten paciencia.\n".encode())

                elif opcion == "7":
                    conexion.send("Gracias por usar la plataforma. ¡Vuelve luego!\n".encode())
                    break

                else:
                    conexion.send("Opción inválida. Intente nuevamente.\n".encode())

        elif typeUser == "ejecutivo":
            conexion.send(f"¡Bienvenido {nombre}! En este momento hay {threading.active_count() - 2} clientes conectados.\n".encode())

        else:
            conexion.send("Credenciales erróneas. Desconectando...\n".encode())

    except Exception as e:
        print(f"[ERROR] {direccion} -> {e}")
    finally:
        conexion.close()
        print(f"[DESCONECTADO] {direccion} se ha desconectado.")

"""
        #No se si esta parte sera necesaria a futuro
        while True:
            data = conexion.recv(1024).decode("utf-8")
            if not data: #Se pierde la conexion con el usuario abruptamente
                break
            elif conexion.close():
                print(f"[DESCONECTADO] {direccion} se ha desconectado.")
            print(f"[{direccion}] {data}")
        """


# Ejecutar el servidor
if __name__ == "__main__":
    revivan_el_server()
