import socket
import threading
import json
from datetime import datetime
import multiprocessing

HOST = "127.0.0.1"
PORT = 5555


lock = threading.Lock()
clientes_esperando = []
emparejamientos = {}
clientes_activos = {}

Filepath = "Data Base.json"

procesos = []

with open("Data Base.json", "r", encoding="utf-8") as archivo:
    dataBase = json.load(archivo)

def guardar_base_datos():
    with open("Data Base.json", "w", encoding="utf-8") as archivo:
        json.dump(dataBase, archivo, indent=4, ensure_ascii=False)

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

        if correo in dataBase.get("clientes", {}) and dataBase["clientes"][correo]["pass"] == password:
            tipo = "cliente"
            nombre_cl = dataBase["clientes"][correo]["nombre"]
            clientes_activos[correo] = {"socket": conn, "nombre": nombre_cl}
            print(f"Cliente {nombre_cl} conectado.")
        elif correo in dataBase.get("ejecutivos", {}) and dataBase["ejecutivos"][correo]["pass"] == password:
            tipo = "ejecutivo"
            nombre_ej= dataBase["ejecutivos"][correo]["nombre"]
            print(f"Ejecutivo {nombre_ej} conectado.")
            
#Funciones para clientes            
        if tipo == "cliente":
            conn.send(f"Asistente: ¡Bienvenido {nombre_cl}! ¿En qué te podemos ayudar?\n".encode())

            while True:
                menu = (
                    "\n[1] Cambio de contraseña\n"
                    "[2] Historial de operaciones\n"
                    "[3] Catálogo / Comprar productos\n"
                    "[4] Solicitar devolución\n"
                    "[5] Confirmar envío\n"
                    "[6] Contactar ejecutivo\n"
                    "[7] Salir\nIngrese una opción: "
                )
                conn.send(menu.encode())
                opcion = conn.recv(1024).decode().strip()

                if opcion == "1":
                    conn.send("Ingrese nueva contraseña: ".encode())
                    new_pass = conn.recv(1024).decode().strip()
                    conn.send("Repita la nueva contraseña: ".encode())
                    confirm = conn.recv(1024).decode().strip()

                    if new_pass == confirm:
                        if new_pass == confirm:
                            dataBase["clientes"][correo]["pass"] = new_pass
                            guardar_base_datos()
                            conn.send("Contraseña actualizada exitosamente.\n".encode())
                            dataBase["clientes"][correo].setdefault("acciones", []).append(f"Cambió su contraseña ({datetime.now().strftime('%d/%m/%Y %H:%M')})")
                            guardar_base_datos()
                        print(f"Cliente {nombre_cl} cambió su contraseña.")
                    else:
                        conn.send("Las contraseñas no coinciden.\n".encode())

                elif opcion == "2":
                    historial = dataBase["clientes"][correo].get("compras", [])
                    dataBase["clientes"][correo].setdefault("acciones", []).append(f"Consultó su historial de compras ({datetime.now().strftime('%d/%m/%Y %H:%M')})")
                    guardar_base_datos()
                    print(f"Cliente {nombre_cl} revisó su historial de compras.")
                    if not historial:
                        conn.send("No hay acciones registradas.\n".encode())
                    else:
                        compras = "\n".join(historial)
                        conn.send(f"Historial:\n{compras}\n".encode())

                elif opcion == "3":
                    dataBase["clientes"][correo].setdefault("acciones", []).append(
                        f"Consultó el catálogo de productos ({datetime.now().strftime('%d/%m/%Y %H:%M')})"
                    )
                    guardar_base_datos()

                    productos = dataBase.get("productos", {})
                    print(f"Cliente {nombre_cl} esta revisando el catálogo de productos.")
                    if not productos:
                        conn.send("No hay productos disponibles.\n".encode())
                    else:
                        lista = "\n".join([f"{pid}: {info['nombre']} - ${info['precio']} - stock[x{info['stock']}]" for pid, info in productos.items()])
                        conn.send(f"Productos disponibles:\n{lista}\nSeleccione ID del producto: ".encode())
                        pid = conn.recv(1024).decode().strip()
                        
                        if pid in productos and productos[pid]["stock"] > 0:
                            producto = productos[pid]
                            #disminuir en una unidad el stock diponible de la carta
                            producto["stock"] -= 1
                            fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
                            nombre_producto = productos[pid]["nombre"]
                            precio = productos[pid]["precio"]
                            registro = f"Compró {nombre_producto} por ${precio} ({fecha})"
                            dataBase["clientes"][correo].setdefault("acciones", []).append(registro)
                            guardar_base_datos()
                            dataBase["clientes"][correo].setdefault("compras", []).append(registro)
                            guardar_base_datos()
                            
                            conn.send("Compra realizada exitosamente.\n".encode())
                            print(f"Cliente {nombre_cl} compró exitosamente {nombre_producto} pid {pid} .")
                        else:
                            conn.send("ID de producto no válido o sin stock.\n".encode())


                elif opcion == "4":
                    conn.send("Ingrese ID del producto a devolver: ".encode())
                    pid = conn.recv(1024).decode().strip()  
                    conn.send("Motivo de la devolución: ".encode())
                    motivo = conn.recv(1024).decode().strip()  

                    conn.send("Solicitud de devolución registrada.\n".encode())
                    dataBase["clientes"][correo].setdefault("acciones", []).append(
                        f"Solicitó devolución del producto ID {pid} con motivo: {motivo} ({datetime.now().strftime('%d/%m/%Y %H:%M')})"
                    )
                    guardar_base_datos()
                    print(f"Cliente {nombre_cl} Solicitó devolución del producto ID {pid} con motivo: {motivo}.")


                elif opcion == "5":
                    conn.send("Confirmación de envío recibida. ¡Gracias por su compra!\n".encode())
                    dataBase["clientes"][correo].setdefault("acciones", []).append(f"Confirmó envío de producto ({datetime.now().strftime('%d/%m/%Y %H:%M')})")
                    guardar_base_datos()
                    print(f"Cliente {nombre_cl} confirmó envío de producto.") 
            
                elif opcion == "6":
                    conn.send("Espere mientras lo conectamos con un ejecutivo...\n".encode())
                    dataBase["clientes"][correo].setdefault("acciones", []).append(f"Solicitó atención de ejecutivo ({datetime.now().strftime('%d/%m/%Y %H:%M')})")
                    guardar_base_datos()

                    with lock:
                        clientes_esperando.append(conn)

                    while True:
                        with lock:
                            if conn in emparejamientos:
                                ejecutivo = emparejamientos[conn]
                                break

                    conn.send("Conectado con un ejecutivo. Escriba 'salir' para terminar el chat.\n".encode())
                    print(f"Cliente {nombre_cl} redirgido con Ejecutivo {nombre_ej}.")
                    while True:
                        msg = conn.recv(1024).decode().strip()
                        if msg.lower() == "salir":
                            break
                        ejecutivo.send(f"Cliente: {msg}\n".encode())

                    conn.send("Chat finalizado.\n".encode())
                    with lock:
                        if conn in emparejamientos:
                            del emparejamientos[ejecutivo]
                            del emparejamientos[conn]

                elif opcion == "7":
                    conn.send("Gracias por usar la plataforma. ¡Hasta luego!\n".encode())
                    print(f"Cliente {nombre_cl} se ha desconectado.")
                    break

                else:
                    conn.send("Opción inválida.\n".encode())

                    
#Accionoes para ejecutivos
                    
        elif tipo == "ejecutivo":
            conn.send(f"Asistente: Hola {nombre_ej}. Hay {len(clientes_esperando)} clientes esperando.\n".encode())

            cliente_actual = None
            atendiendo=False

            while True:
                conn.send(f"Ingrese algún comando".encode())
                menu_ej = (
                    "\n[:status] Consultar solicitudes\n"
                    "[:connect] conectarse con uncliente en espera\n"
                    "[:details] Consultar última acción de clientes áctivos\n"
                    "[:history] Revisar historial del cliente\n"
                    "[:operations] Mostrar historial de operaciones al cliente\n"
                    "[:catalogue] Consultar catálogo disponible\n"
                    "[:buy] Comprar carta al cliente [carta, precio]\n"
                    "[:publish] Publicar una carta a la venta (en caso de no estar catalogada indicar precio)\n "
                    "[:disconnect] Terminar conexión con cliente\n"
                    "[:exit] Salir\nIngrese una opción: "
                )
                conn.send(menu_ej.encode())
                comando = conn.recv(1024).decode().strip()
                
                if comando == ":status":
                    conn.send(f"Clientes conectados: {len(clientes_activos)}\nSolicitudes en espera: {len(clientes_esperando)}\n".encode())

                elif comando == ":details":
                    if not clientes_activos:
                        conn.send("No hay clientes conectados.\n".encode())
                    else:
                        detalles = ""
                        for mail, info in clientes_activos.items():
                            detalles += f"{mail} - {info['nombre_cl']} | Última acción: {info.get('ultima_accion', 'Sin actividad')}\n"
                        conn.send(detalles.encode())

                elif comando == ":connect":
                    with lock:
                        if not clientes_esperando:
                            conn.send("No hay clientes esperando actualmente.\n".encode())
                            continue
                        atendiendo=True
                        cliente_atendido = clientes_esperando.pop(0)
                        emparejamientos[cliente_atendido] = conn
                        emparejamientos[conn] = cliente_atendido
                    conn.send("Conectado con un cliente. Puede comenzar a chatear. (:disconnect para terminar)\n".encode())

                elif comando == ":history":
                    if atendiendo== False:
                        conn.send("No estás atendiendo a ningún cliente.\n".encode())
                        continue
                    for correo, data in clientes_activos.items():
                        if data["socket"] == cliente_atendido:
                            historial = dataBase["clientes"][correo].get("acciones", [])
                            if not historial:
                                conn.send("El cliente no tiene historial.\n".encode())
                            else:
                                conn.send("\n".join(historial).encode())
                            break

                elif comando == ":operations":
                    if atendiendo== False:
                        conn.send("No estás atendiendo a ningún cliente.\n".encode())
                        continue
                    for correo, data in clientes_activos.items():
                        if data["socket"] == cliente_atendido:
                            compras = dataBase["clientes"][correo].get("compras", [])
                            if not compras:
                                conn.send("El cliente no tiene operaciones.\n".encode())
                            else:
                                conn.send("\n".join(compras).encode())
                            break

                elif comando == ":catalogue":
                    productos = dataBase.get("productos", {})
                    if not productos:
                        conn.send("Catálogo vacío.\n".encode())
                    else:
                        lista = "\n".join([f"{pid}: {info['nombre']} - ${info['precio']} - stock[x{info['stock']}]" for pid, info in productos.items()])
                        conn.send(lista.encode())

                elif comando.startswith(":buy "):
                    if atendiendo== False:
                        conn.send("No estás atendiendo a ningún cliente.\n".encode())
                        continue
                    partes = comando.split(" ")
                    if len(partes) < 3:
                        conn.send("Uso incorrecto: :buy [carta] [precio]\n".encode())
                        continue
                    carta = partes[1]
                    precio = partes[2]
                    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
                    registro = f"Compra de {carta} por ${precio} ({fecha})"
                    for correo, data in clientes_activos.items():
                        if data["socket"] == cliente_atendido:
                            dataBase["clientes"][correo].setdefault("compras", []).append(registro)
                            dataBase["clientes"][correo].setdefault("acciones", []).append(f"Compró {carta} por ${precio}")
                            guardar_base_datos()
                            cliente_atendido.send(f"Compra registrada: {carta} por ${precio}\n".encode())
                            #Se suma una unidad de la carta al stock disponible
                            producto = productos[pid]
                            producto["stock"] += 1
                            pid = conn.recv(1024).decode().strip()
                            conn.send("Compra registrada.\n".encode())
                            break

                elif comando.startswith(":publish "):
                    partes = comando.split(" ")
                    if len(partes) < 3:
                        conn.send("Uso incorrecto: :publish [carta] [precio]\n".encode())
                        continue
                    carta = partes[1]
                    precio = partes[2]
                    pid = str(len(dataBase["productos"]) + 1)
                    dataBase["productos"][pid] = {"nombre": carta, "precio": precio}
                    guardar_base_datos()
                    conn.send(f"{carta} publicada por ${precio}.\n".encode())

                elif comando == ":disconnect":
                    if atendiendo== True:
                        cliente_atendido.send("Chat finalizado por el ejecutivo.\n".encode())
                        with lock:
                            del emparejamientos[conexion]
                            del emparejamientos[cliente_atendido]
                        cliente_atendido = None
                        atendiendo== False
                        conn.send("Desconectado del cliente.\n".encode())
                    else:
                        conn.send("No hay cliente conectado actualmente.\n".encode())

                elif comando == ":exit":
                    conn.send("Desconectando...\n".encode())
                    break

                elif cliente_atendido:
                    cliente_atendido.send(f"Ejecutivo: {comando}\n".encode())

                else:
                    conn.send("Comando no reconocido o sin cliente conectado.\n".encode())

        else:
            conn.send("Credenciales incorrectas. Desconectando...\n".encode())

    except Exception as e:
        print(f"[ERROR] {direccion}: {e}")

    finally:
        conn.close()
        print(f"[DESCONECTADO] {direccion}")

def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((HOST, PORT))
    servidor.listen(10)
    print(f"[SERVIDOR] Escuchando en {HOST}:{PORT}...")

    while True:
        conn, addr = servidor.accept()  # Aceptar nuevas conexiones
        hilo = threading.Thread(target=manejar_usuario, args=(conn, addr))  # Crear hilo para cada conexión
        hilo.start()
        print(f"[SERVIDOR] Conexiones activas: {threading.active_count() - 1}")

                

if __name__ == "__main__":
    servidor_hilo = threading.Thread(target=iniciar_servidor)
    servidor_hilo.start()
    #Se abre un rango de hasta 14 conexiones simultaneas
    for direccion in range(1, 15):
            proceso = multiprocessing.Process(target=manejar_usuario, args=(HOST, PORT))
            procesos.append(proceso)
            proceso.start()
    # Esperar a que todos los procesos terminen
            for proceso in procesos:
                proceso.join()

