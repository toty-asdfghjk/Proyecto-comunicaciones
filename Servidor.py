import socket
import threading
import json
from datetime import datetime

#Se configura el servidor para que corra localmente
HOST = "127.0.0.1"
PORT = 5555

bases = open("Data Base.json", "r")
dataBase = json.load(bases)

#Se crea el socket y se instancia en las variables anteriores
def revivan_el_server():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((HOST, PORT))
    servidor.listen(15) #Capacidad de conexiones (creo)
    print("[SERVIDOR] Esperando conexiones...")

    while True:
        conexion, direccion = servidor.accept()
        thread = threading.Thread(target=clientesConect, args=(conexion, direccion)) #para contar usuarios
        thread.start()
        print(f"[SERVIDOR] Conexiones activas: {threading.active_count() - 1}") #contador de usuarios conectados

#Funcion para manejar a los clientes (ejecutivos tambien) con thread
def clientesConect(conexion, direccion):
    print(f"[NUEVA CONEXIÓN] {direccion} conectado.")

    try:
        #Bienvenida + login
        conexion.send(("¡Bienvenido a la plataforma de servicio al cliente de la tienda TC5G! \n"
                      "Para autenticarse ingrese su mail y contraseña: \n"
                      "Correo: ").encode()) #envio de mensaje al usuario
        correo = conexion.recv(1024).decode().strip()
        conexion.send("Ingrese su contraseña: ".encode()) #envio de mensaje al usuario
        password = conexion.recv(1024).decode().strip()

        typeUser = None #para guardar si el usuario es cliente o ejecutivo
        Nombre = None #para guardar el nombre del usuario

        #Proceso de validacion de credenciales
        if correo in dataBase["clientes"]: #correo encontrado en la base de datos de usuario
            if dataBase["clientes"][correo]["pass"] == password: #contraseña correcta
                typeUser = "cliente" #usuario es cliente
                nombre = dataBase["clientes"][correo]["nombre"] #se guarda el nombre para referirse a el usuario


        elif correo in dataBase["ejecutivos"]: #correo encontrado en la base de datos de ejecutivos
            if dataBase["ejecutivos"][correo]["pass"] == password: #contraseña correcta
                typeUser = "ejecutivo" #usuario es ejecutivo
                nombre = dataBase["ejecutivos"][correo]["nombre"] #se guarda el nombre para referirse a el usuario
        
        

        #Si paso las credenciales, se le asigna su respectivo menu
        if typeUser == "cliente": #usuario es cliente (requiere menu para clientes)
            conexion.send(f"Asistente: ¡Bienvenido {nombre}! ¿En que te podemos ayudar?".encode()) #envio de mensaje al usuario
            while True
                #---------Menu cliente---------#
                menu = ("[1] Cambio de contraseña. \n"
                        "[2] Historial de operaciones. \n"
                        "[3] Catalogo de productos / Comprar productos. \n"
                        "[4] Solicitar devolucion. \n"
                        "[5] Confirmar envio. \n"
                        "[6] Contactarse con un ejecutivo. \n"
                        "[7] Salir \n"
                        "Ingrese un numero: \n")
                conexion.send(menu.encode()) #envio de mensaje al usuario
                opcion = conexion.recv(1024).decode().strip() #mensaje desde el usuario

                #Desafio mayormente en opcion 2 (mostrar y seleccionar una compra del historial), 
                #opcion 3 (registrar bien el formato de compra y armar la lista de productos en database)
                #opcion 6 (armar sala de chat con ejecutivo)

                if opcion == "1":
                    conexion.send("Ingrese nueva contraseña: ".encode()) #envio de mensaje al usuario
                    newPassword =conexion.recv(1024).decode().strip() #mensaje desde el usuario
                    conexion.send("Ingrese su nueva contraseña otra vez: ".encode()) #envio de mensaje al usuario
                    newPassword2 =conexion.recv(1024).decode().strip() #mensaje desde el usuario
                    if newPassword == newPassword2:
                        dataBase["clientes"][correo]["pass"] = newPassword #se actualiza la contraseña
                        conexion.send("Contraseña actualizada exitosamente. \n".encode()) #envio de mensaje al usuario
                    else:
                        conexion.send("Las contraseñas no coinciden. Se le regresara al menu. \n".encode()) #envio de mensaje al usuario

                elif opcion == "2":
                    historial = dataBase["clientes"][correo].get("compras", []) #se obtiene la lista del historial
                    if not historial:
                        conexion.send("No hay operaciones registradas. \n".encode()) #envio de mensaje al usuario
                    else:
                        compras = "\n".join(historial) #se separa la lista del historial
                        conexion.send(f"Compras: \n{compras}\n".encode()) #envio de mensaje al usuario

                elif opcion == "3":
                    productos = dataBase.get("productos", {}) #se obtienen los productos
                    if not productos:
                        conexion.send("No hay productos disponibles en este momento. \n".encode()) #envio de mensaje al usuario
                    else:
                        lista = "\n".join([f"prodID: {info["nombre"]} - {info["precio"]}" for prodID, info in productos.items()]) #se separa la lista de los productos
                        conexion.send(f"Productos disponibles: \n{lista} \n","Seleccione ID del producto que desea: ".encode()) #envio de mensaje al usuario
                        prodID = conexion.recv(1024).decode().strip() #mensaje desde el usuario
                        if prodID in productos:
                            fecha = datetime.now().strftime("%d/%m/%Y $H:$M") #formato a la fecha
                            producto = productos[prodID]["nombre"] #se obtiene el producto
                            registro = f"{producto}" ({fecha}) #se guarda el formato de guardado del producto
                            dataBase["clientes"][correo].setdefault("compras", []).append(registro) #se añade a la lista de compras
                        else:
                            conexion.send("ID invalido. \n".encode()) #envio de mensaje al usuario

                elif opcion == "4":
                    conexion.send("Ingrese ID del producto a devolver: \n".encode()) #envio de mensaje al usuario
                    prodID = conexion.recv(1024).decode().strip() #mensaje desde el usuario
                    conexion.send("Motivo de la devolucion: \n".encode()) #envio de mensaje al usuario
                    motivo = conexion.recv(1024).decode().strip()  #mensaje desde el usuario
                    conexion.send("Solicitud de devolucion registrada. Lamentamos los inconvenientes 😔. \n".encode()) #envio de mensaje al usuario

                elif opcion == "5":
                    conexion.send("Confirmacion de envio recibida. ¡Gracias por comprar con nosotros! \n".encode()) #envio de mensaje al usuario

                elif opcion == "6":
                    conexion.send("Un ejecutivo se comunicara contigo pronto, por favor ten paciencia. \n".encode()) #envio de mensaje al usuario
                    #Implementar chat con ejecutivo posteriormente

                elif opcion == "7":
                    conexion.send("Gracias por usar la plataforma. ¡Vuelve luego!  \n".encode()) #envio de mensaje al usuario

                else:
                    conexion.send("Opcion invalida. Intente nuevamente. \n".encode()) #envio de mensaje al usuario





        elif typeUser == "ejecutivo": #usuario es ejecutivo (requiere menu para ejecutivo)
            conexion.send(f"¡Bienvenido {nombre}! en este momento hay N_clientes conectados.".encode()) #envio de mensaje al usuario






        elif typeUser == None:
            conexion.send("Credenciales erroneas. Desconectando...".encode()) #envio de mensaje al usuario

            conexion.close()

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

    except:
        conexion.close()
        print(f"[DESCONECTADO] {direccion} se ha desconectado.")

# Arrancar el servidor
if __name__ == "__main__":
    revivan_el_server()