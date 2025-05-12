#se importan librerias
import socket
import threading
import json
from datetime import datetime
import multiprocessing

#se definen puertos de conexion
HOST = "127.0.0.1"
PORT = 5555

#se definen variables globales
mutex= threading.Lock()
emparejamientos = {}
clientes_activos = {}
clientes_esperando = []
clientes_conectados=[]
ejecutivos_conectados=[]
ejecutivos_activos = {}

Filepath = "Data Base.json"

procesos = []

#se lee la base de datos
with open("Data Base.json", "r", encoding="utf-8") as archivo:
    dataBase = json.load(archivo)

def guardar_base_datos():
    with open("Data Base.json", "w", encoding="utf-8") as archivo:
        json.dump(dataBase, archivo, indent=4, ensure_ascii=False)

def eliminar_usuario(conn, tipo):
    if tipo == "cliente":
        
        for idx, (_, c) in enumerate(clientes_conectados):
            if c == conn:
                
                del clientes_conectados[idx]
                break
    elif tipo == "ejecutivo":
        for idx, (_, e) in enumerate(ejecutivos_conectados):
            if e == conn:
                del ejecutivos_conectados[idx]
                break

def manejar_chat(conn, nombre, es_ejecutivo=False):
    #maneja la comunicación, con soporte para comandos de ejecutivo
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
                
            msg = data.decode().strip()
            
            # Comandos de desconexión
            if msg.lower() in ("salir", ":disconnect"):
                conn.send("Confirmando desconexión...\n".encode())
                break
                
            # Si es ejecutivo, verifica comandos especiales
            if es_ejecutivo and msg.startswith(':'):
                with mutex:
                    #comandos durante chat
                    if conn in emparejamientos:
                        pareja = emparejamientos[conn]

                        #revisa el historial de acciones del cliente
                        if msg == ":history": 
                            for correo, data in clientes_activos.items(): #se obtienen datos del cliente 
                                if data["socket"] == pareja: #se corrobora si el cliente esta siendo atendido por un ejecutivo en este momento
                                    historial = dataBase["clientes"][correo].get("acciones", []) #se obtiene las acciones del cliente
                                    if not historial: #el cliente no ha realizado acciones 
                                        conn.send("El cliente no tiene historial.\n".encode())
                                    else:
                                        conn.send("\n".join(historial).encode()) #se ajustan las acciones realizadas por el cliente para printear
                                    break

                        #revisa las compras del cliente
                        elif msg == ":operations": 
                            for correo, data in clientes_activos.items(): #se obtienen datos del cliente en caso de estar conectado al server
                                if data["socket"] == pareja: #se corrobora si el cliente esta siendo atendido por un ejecutivo en este momento
                                    compras = dataBase["clientes"][correo].get("compras", []) #se obtienen las compras realizadas por el cliente
                                    if not compras: #el cliente no tiene compras
                                        conn.send("El cliente no tiene operaciones.\n".encode())
                                    else:
                                        conn.send("\n".join(compras).encode()) #se ajustan las compras del cliente para printear
                                    break

                        #Comprar carta al cliente [carta, precio]
                        elif msg.startswith(":buy"): 
                            partes = msg.split(" ") #se separan el comando en [comando],[nombre_carta],[precio]
                            if len(partes) < 3: #si hay mas de 3 palabras el comando no se ingreso bien
                                conn.send("Uso incorrecto: :buy [carta] [precio]\n".encode())
                                continue #se sale del bloque if
                                    
                            carta = partes[1].strip() #nombre de la carta
                            precio = partes[2].strip() #precio de la carta 
                            fecha = datetime.now().strftime("%d/%m/%Y %H:%M") #se guarda la fecha de la compra
                            try: #puede darse error comun en la definicion de precio
                                precio = float(precio)
                            except:
                                conn.send("ERROR: el precio debe ser un valor numerico (usar '.' para decimales)\n".encode()) #en particular al poner decimales con "," en lugar de "."
                                continue

                            for correo, data in clientes_activos.items(): #se obtienen datos del cliente en caso de estar conectado al server
                                if data["socket"] == pareja: #se corrobora si el cliente esta siendo atendido por un ejecutivo en este momento
                                    carta_exist = False
                                    items_cl = dataBase["clientes"][correo].get("items", {})
                                    for pid, item in items_cl.items():
                                        if item["nombre"].lower() == carta.lower():
                                            carta_exist = True
                                            if item["unidades"] > 0:
                                                item["unidades"] -= 1
                                            
                                    if carta_exist:
                                            registro_compra = f"Venta de {carta} por ${precio} ({fecha})"
                                            registro_accion = f"Vendió {carta} por ${precio}"
                                            dataBase["clientes"][correo].setdefault("compras", []).append(registro_compra)
                                            dataBase["clientes"][correo].setdefault("acciones", []).append(registro_accion)
                                            conn.send(f"compra registrada: {carta} por ${precio}\n".encode())
                                            pareja.send(f"El ejecutivo ha comprado tu {carta} por ${precio}\n".encode())
                                            break
                                    else: 
                                        conn.send(f"El cliente no tiene {carta} en su posesión.\n".encode())
                                break

                        #comando para desconectarse del chat
                        elif msg == ":disconnect":
                            pareja.send("El ejecutivo terminó la conversación.\n".encode())
                            break

                        #no se identifico un comando o no es disponible de usar durante el chat
                        else:
                            conn.send("Comando no reconocido (:status, :details, :catalogue, :publish solo estan disponible fuera del modo chat).\n".encode())
            # Reenvío normal de msgs
            with mutex:
                if conn in emparejamientos:
                    pareja = emparejamientos[conn]
                    if es_ejecutivo and msg.startswith(':'):
                        pareja.send(f"{nombre}: [COMANDO]")
                    pareja.send(f"{nombre}: {msg}\n".encode())
                    
        except Exception as e:
            print(f"[ERROR] Chat {nombre}: {e}")
            break
            
    # Limpieza post-desconexión
    with mutex:
        if conn in emparejamientos:
            del emparejamientos[emparejamientos[conn]]
            del emparejamientos[conn]


#funcion para login de usuario
def manejar_usuario(conn, direccion):
    print(f"[NUEVA CONEXIÓN] {direccion} conectado.")
    try:
        conn.send("¡Bienvenido a la tienda TC5G!\n Por favor ingrese su correo: ".encode())
        correo = conn.recv(1024).decode().strip()

        conn.send("Ingrese su contraseña: ".encode())
        password = conn.recv(1024).decode().strip()
            
        tipo = None
        nombre_cl = None
        nombre_ej = None

        #se separan casos de usuario (cliente o ejecutivo)
        if correo in dataBase.get("clientes", {}) and dataBase["clientes"][correo]["pass"] == password:
            tipo = "cliente"
            nombre_cl = dataBase["clientes"][correo]["nombre"]
            clientes_activos[correo] = {"socket": conn, "nombre": nombre_cl}
            clientes_conectados.append((nombre_cl, conn))
            print(f"Cliente {nombre_cl} conectado.")
        elif correo in dataBase.get("ejecutivos", {}) and dataBase["ejecutivos"][correo]["pass"] == password:
            tipo = "ejecutivo"
            nombre_ej= dataBase["ejecutivos"][correo]["nombre"]
            ejecutivos_activos[correo] = {"socket": conn, "nombre": nombre_ej}
            ejecutivos_conectados.append((nombre_ej, conn))
            print(f"Ejecutivo {nombre_ej} conectado.")


############### SECCION PARA CLIENTES ###############
    #Funciones para clientes            
        if tipo == "cliente": #se detecto usuario en clientes
            conn.send(f"Asistente: ¡Bienvenido {nombre_cl}! ¿En qué te podemos ayudar?\n".encode())

            #Menu y oppciones para clientes
            while True:
                menu = (
                    "\n[1] Cambio de contraseña\n"
                    "[2] Historial de operaciones\n"
                    "[3] Catálogo / Comprar productos\n"
                    "[4] Solicitar devolución\n"
                    "[5] Confirmar envío\n"
                    "[6] Contactar ejecutivo\n"
                    "[7] Salir\nIngrese una opción: ")
                conn.send(menu.encode())
                opcion = conn.recv(1024).decode().strip() #opcion seleccionada por el cliente

                if opcion == "1": #Cambio de contraseña
                    conn.send("Ingrese nueva contraseña: ".encode())
                    new_pass = conn.recv(1024).decode().strip() #primer ingreso de contraseña nueva
                    conn.send("Repita la nueva contraseña: ".encode())
                    confirm = conn.recv(1024).decode().strip() #segundo ingreso de contraseña nueva

                    if new_pass == confirm: #se verifica que ambas contraseñas ingresadas coinciden
                        dataBase["clientes"][correo]["pass"] = new_pass #se modifica la contraseña
                        guardar_base_datos() #se actualiza la contraseña en la base de datos
                        conn.send("Contraseña actualizada exitosamente.\n".encode())
                        dataBase["clientes"][correo].setdefault("acciones", []).append(f"Cambió su contraseña ({datetime.now().strftime('%d/%m/%Y %H:%M')})") #se registra accion del cliente
                        guardar_base_datos() #se actualiza la base de datos
                        print(f"Cliente {nombre_cl} cambió su contraseña.")
                    else:
                        conn.send("Las contraseñas no coinciden.\n".encode())

                #Historial de operaciones
                elif opcion == "2":
                    historial = dataBase["clientes"][correo].get("compras", []) #se guarda el historial de compras en una variable auxiliar
                    dataBase["clientes"][correo].setdefault("acciones", []).append(f"Consultó su historial de compras ({datetime.now().strftime('%d/%m/%Y %H:%M')})") #se registra accion del cliente
                    guardar_base_datos() #se actualiza la base de datos
                    print(f"Cliente {nombre_cl} revisó su historial de compras.")
                    if not historial: #el cliente no tiene compras realizadas
                        conn.send("No hay compras registradas.\n".encode())
                    else: #el cliente tiene compras realizadas
                        compras = "\n".join(historial) #se ajusta la lista de compras para printear
                        conn.send(f"Historial:\n{compras}\n".encode())

                #Catálogo / Comprar productos
                elif opcion == "3":
                    dataBase["clientes"][correo].setdefault("acciones", []).append(
                        f"Consultó el catálogo de productos ({datetime.now().strftime('%d/%m/%Y %H:%M')})"
                    ) #se registra accion del cliente
                    guardar_base_datos() #se actualiza la base de datos

                    productos = dataBase.get("productos", {}) #se guarda el catalogo de productos en una variable auxiliar 
                    print(f"Cliente {nombre_cl} esta revisando el catálogo de productos.")
                    if not productos: #no hay productos en el catalogo
                        conn.send("No hay productos disponibles.\n".encode())
                    else: #si hay productos en el catalogo
                        lista = "\n".join([f" {pid}: {info['nombre']} - ${info['precio']} - stock[x{info['stock']}]" for pid, info in productos.items()]) #se ajustan el catalogo para printear
                        conn.send(f"Productos disponibles:\n{lista}\nSeleccione ID del producto: ".encode())
                        pid = conn.recv(1024).decode().strip() #se obtiene el ID del producto del usuario
                            
                        if pid in productos and productos[pid]["stock"] > 0: #se verifica si el producto tiene stock
                            producto = productos[pid] #se guarda ID del producto
                            producto["stock"] -= 1 #disminuir en una unidad el stock diponible de la carta
                            fecha = datetime.now().strftime("%d/%m/%Y %H:%M")#se guarda fecha de la accion
                            nombre_producto = productos[pid]["nombre"] #se guarda nombre del producto
                            precio = productos[pid]["precio"] #se guarda precio del producto
                            registro = f" Compró {nombre_producto} ID:{pid} por ${precio} ({fecha}) " #accion hecha por el cliente
                            dataBase["clientes"][correo].setdefault("acciones", []).append(registro) #se registra accion del cliente
                            guardar_base_datos() #se actualiza la base de datos
                            dataBase["clientes"][correo].setdefault("compras", []).append(registro) #se registra en el historial del cliente la compra realizada
                            guardar_base_datos() #se actualiza la base de datos
                            print(f"Cliente {nombre_cl} compró exitosamente {nombre_producto} ID {pid} .")
                            carta_exist = False #detector de existencia de la carta en la cuenta del usuario
                            articulos = dataBase["clientes"][correo].get("items",{}) #se obtiene el catalogo
                            for pid, info in articulos.items(): #se recorre la lista de items
                                if info["nombre"].lower() == nombre_producto.lower(): #se verifica si la carta esta en el catalogo
                                    info["unidades"] += 1 #se suma 1 al stock
                                    conn.send("Compra realizada exitosamente.\n".encode())
                                    carta_exist = True #la carta fue detectada en el catalogo
                                    guardar_base_datos() #se actualiza la base de datos
                                    break
                            if not carta_exist: #la carta no existe en el catalogo
                                pid = str(len(dataBase["clientes"][correo]["items"]) + 1) #se crea codigo del item
                                dataBase["clientes"][correo]["items"][pid] = {"unidades": 1, "nombre": carta} #se crea el producto y se incluye al catalogo
                                guardar_base_datos() #se actualiza la base de datos
                                conn.send(f" nueva{carta} registrada con exito.\n".encode())
                        
                        else:
                            conn.send("ID de producto no válido o sin stock.\n".encode()) #producto sin stock

                #Solicitar devolución
                elif opcion == "4":
                    conn.send("Ingrese ID del producto a devolver: ".encode())
                    pid = conn.recv(1024).decode().strip()
                    boleta = dataBase["clientes"][correo].get("compras",[])
                    articulos = dataBase["clientes"][correo].get("items",{})
                    articulo= articulos[pid]
                    if not articulo:
                        conn.send("Producto no encontrado en su inventario. \n")
                        continue
                    elif articulo["unidades"] > 0:
                        conn.send("Motivo de la devolución: ".encode())
                        motivo = conn.recv(1024).decode().strip()  

                        conn.send("Solicitud de devolución registrada.\n".encode())
                        dataBase["clientes"][correo].setdefault("acciones", []).append(
                            f"Solicitó devolución del producto ID  {pid} con motivo: {motivo} ({datetime.now().strftime('%d/%m/%Y %H:%M')})"
                        ) #se registra accion del cliente
                        guardar_base_datos() #se actualiza la base de datos
                            
                        print(f"Cliente {nombre_cl} Solicitó devolución del producto ID {pid} con motivo: {motivo}.")
                        
                        productos = dataBase.get("productos", {}) #se obtiene el catalogo
                        producto = productos[pid] #se guarda ID del producto
                        producto["stock"] += 1 #se suma 1 al stock
                        articulo["unidades"]-=1
                        guardar_base_datos() #se actualiza la base de datos
                    else:
                        conn.send("Usted no ha comprado o no posee el producto mencionado".encode())
                    ###### ¿detectar si la carta que devuelve esta en la base de datos y añadirlo? ######
                    ###### Algo similar a buy y publish de la parte del ejecutivo ######
                    

                #Confirmar envío
                elif opcion == "5":
                    conn.send("Confirmación de envío recibida. ¡Gracias por su compra!\n".encode())
                    dataBase["clientes"][correo].setdefault("acciones", []).append(f"Confirmó envío de producto ({datetime.now().strftime('%d/%m/%Y %H:%M')})") #se registra accion del cliente
                    guardar_base_datos() #se actualiza la base de datos
                    print(f"Cliente {nombre_cl} confirmó envío de producto.") 

                #Contactar ejecutivo
                elif opcion == "6": ##### Falta que funcione, la idea esta y la logica del codigo permite comunicacion uno a uno (cliente/ejecutivo) #####
                    conn.send("Espere mientras lo conectamos con un ejecutivo...\n".encode())
                    dataBase["clientes"][correo].setdefault("acciones", []).append(f"Solicitó atención de ejecutivo ({datetime.now().strftime('%d/%m/%Y %H:%M')})") #se registra accion del cliente
                    guardar_base_datos() #se actualiza la base de datos

                    with mutex:
                        clientes_esperando.append((nombre_cl,conn)) #se añade cliente a la lista de espera

                    while True:
                        with mutex:
                            if conn in emparejamientos:
                                conn_cl = conn
                                nombre_ej, conn_ej = ejecutivos_conectados.pop(0)
                                #se empareja ejecutivo con cliente
                                emparejamientos[conn_cl] = conn_ej
                                emparejamientos[conn_ej] = conn_cl
                                print(nombre_cl, " ; ", conn_cl, " ; ", nombre_ej, " ; ", conn_ej)
                                print(f"Cliente {nombre_cl} redirgido con Ejecutivo {nombre_ej}.")
                                break

                    conn.send("Conectado con un ejecutivo. Escriba 'salir' para terminar el chat.\n".encode())
                    manejar_chat(conn, nombre_cl)
                    continue
                #Salir
                elif opcion == "7": #cliente se desconecta
                    conn.send("Gracias por usar la plataforma. ¡Hasta luego!\n".encode())
                    eliminar_usuario(conn,tipo)
                    del clientes_activos[correo]
                    print(f"Cliente {nombre_cl} se ha desconectado.")
                    break

                else:
                    conn.send("Opción inválida.\n".encode())

                        
############### SECCION PARA EJECUTIVOS ###############
    #Funciones para ejecutivos               
        elif tipo == "ejecutivo": #el usuario se hace login como ejecutivo
            conn.send(f"Asistente: Hola {nombre_ej}. Hay {len(clientes_esperando)} clientes esperando.\n".encode())

                
            atendiendo=False #variable para detectar modo chat con cliente
            conn.send(f"Ingrese algún comando".encode())
            #Menu para ejecutivo
            menu_ej = (
                "\n[:status] Consultar solicitudes\n"
                "[:connect] Conectarse con uncliente en espera\n"
                "[:details] Consultar última acción de clientes áctivos\n"
                "[:history] Revisar historial del cliente\n"
                "[:operations] Mostrar historial de operaciones al cliente\n"
                "[:catalogue] Consultar catálogo disponible\n"
                "[:buy] Comprar carta al cliente [carta, precio]\n"
                "[:publish] Publicar una carta a la venta (en caso de no estar catalogada indicar precio)\n"
                "[:disconnect] Terminar conexión con cliente\n"
                "[:exit] Salir\n"
            )
            conn.send(menu_ej.encode())

            while True: 
                if atendiendo == False:
                    conn.send("Ingrese una opción: ".encode())
                else: conn.send("\u200A".encode())

                comando = conn.recv(1024).decode().strip()

                #Consultar solicitudes
                if comando == ":status": 
                    conn.send(f"Clientes conectados: {len(clientes_activos)}\nSolicitudes en espera: {len(clientes_esperando)}\n".encode())

                #Consultar última acción de clientes áctivos
                elif comando == ":details": 
                    if not clientes_activos: #no hay clientes
                        conn.send("No hay clientes conectados.\n".encode())
                    else: #hay clientes conectados
                        detalles = ""
                        for mail, info in clientes_activos.items(): #se extraen datos de los usuarios activos
                            detalles += f"{mail} - {info['nombre']} | Última acción: {info.get('ultima_accion', 'Sin actividad')}\n"
                        conn.send(detalles.encode())

                    #Conectarse con un cliente en espera
                elif comando == ":connect": 
                    with mutex:
                        if not clientes_esperando: #no hay clientes esperando contactarse
                            conn.send("No hay clientes esperando actualmente.\n".encode())
                        else:
                            atendiendo=True #se activa el comando para modo chat
                            nombre_cl, conn_cl = clientes_esperando.pop(0) #se saca al cliente de la lista
                            conn_ej = conn
                        
                            emparejamientos[conn_cl] = conn_ej #se establece al cliente como que esta siendo atendido
                            emparejamientos[conn_ej] = conn_cl
                            cliente_atendido = conn_cl
                            conn.send("Conectado con un cliente. Puede comenzar a chatear. (':disconnect' para terminar)\n".encode())
                            conn_cl.send("Un ejecutivo se ha conectado. Puede comenzar a chatear. ('salir' para terminar)\n".encode())
                    
                    manejar_chat(conn, nombre_ej, True)
                    continue

                #Revisar historial de compras del cliente
                elif comando == ":history": 
                    if atendiendo == False: #no se esta atendiendo a cliente
                        conn.send("No estás atendiendo a ningún cliente.\n".encode())
                        continue #se sale del bloque if

                #Mostrar historial de operaciones al cliente
                elif comando == ":operations": 
                    if atendiendo== False: #no se esta atendiendo a cliente
                        conn.send("No estás atendiendo a ningún cliente.\n".encode())
                        continue #se sale del bloque if

                #Consultar catálogo disponible
                elif comando == ":catalogue": 
                    productos = dataBase.get("productos", {}) #se obtiene el catalogo de productos
                    if not productos: #si no hay catalogo
                        conn.send("Catálogo vacío.\n".encode())
                    else:
                        lista = "\n".join([f"{pid}: {info['nombre']} - ${info['precio']} - stock[x{info['stock']}]" for pid, info in productos.items()]) #se ajustan los productos para printear
                        conn.send(lista.encode())

                #Comprar carta al cliente [carta, precio]
                elif comando.startswith(":buy"): 
                    if atendiendo== False: #no se esta atendiendo a cliente
                        conn.send("No estás atendiendo a ningún cliente.\n".encode())
                        continue #se sale del bloque if      

                #Publicar una carta a la venta
                elif comando.startswith(":publish "): 
                    partes = comando.split(" ") #se separan el comando en [comando],[nombre_carta],[precio]
                    if len(partes) < 3: #si hay mas de 3 palabras el comando no se ingreso bien
                        conn.send("Uso incorrecto: :publish [carta] [precio]\n".encode())
                            
                    carta = partes[1] #nombre de la carta
                    precio = partes[2] #precio de la carta 
                    carta_exist = False #detector de existencia de la carta en el catalogo
                    productos = dataBase.get("productos", {}) #se obtiene el catalogo
                    for pid, info in productos.items(): #se recorre la lista de productos
                        if info["nombre"].lower() == carta.lower(): #se verifica si la carta esta en el catalogo
                            info["stock"] += 1 #se suma 1 al stock
                            info["precio"] = float(precio) #se actualiza o mantiene el precio
                            conn.send(f"Producto {carta} publicado con precio ${precio}.\n".encode())
                            carta_exist = True #la carta fue detectada en el catalogo
                            guardar_base_datos() #se actualiza la base de datos
                            break
                    if not carta_exist: #la carta no existe en el catalogo
                        pid = str(len(dataBase["productos"]) + 1) #se crea codigo del producto
                        dataBase["productos"][pid] = {"stock": 1, "nombre": carta, "precio": float(precio)} #se crea el producto y se incluye al catalogo
                        guardar_base_datos() #se actualiza la base de datos
                        conn.send(f"{carta} publicada por ${precio}.\n".encode())

                    #Terminar conexión con cliente
                elif comando == ":disconnect": 
                    conn.send("No hay cliente conectado actualmente.\n".encode())

                #Se desconecta el ejecutivo
                elif comando == ":exit":
                    eliminar_usuario(conn,tipo)
                    conn.send("Desconectando...\n".encode())
                    print(f"Ejecutivo {nombre_ej} se ha desconectado.")
                    break

                else:
                    conn.send("Comando no reconocido o sin cliente conectado.\n".encode())

        else:
            conn.send("Credenciales incorrectas. Desconectando...\n".encode())

            

    except Exception as e: #deteccion de errores
        print(f"[ERROR] {direccion}: {e}")

    finally: #deteccion de errores
        conn.close()
        print(f"[DESCONECTADO] {direccion}")

### SE INICIA EL SERVIDOR ###
def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((HOST, PORT))
    servidor.listen()
    print(f"[SERVIDOR] Escuchando en {HOST}:{PORT}...")

    while True:
        conn, addr = servidor.accept()  # Aceptar nuevas conexiones
        hilo = threading.Thread(target=manejar_usuario, args=(conn, addr))  # Crear hilo para cada conexión
        hilo.start()
        print(f"[SERVIDOR] Conexiones activas: {threading.active_count() - 1}")

                

if __name__ == "__main__":
    iniciar_servidor()
