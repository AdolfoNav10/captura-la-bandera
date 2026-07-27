import socket
import threading
import time
import json
from src.comun import protocolo as p
from src.comun import registro

PUERTO_DEFECTO = 8889

conexion_servidor = None

ultimo_state = {"players": [], "flag": {"owner": None, "x": 500, "y": 500}}
config_juego = {"map_size": 1000, "circle_radius": 300, "player_radius": 15}
estado_cliente = {
    "conectado": False,
    "error": None,
    "fase": "lobby",
    "countdown": None,
    "mi_id": None,
    "mi_nombre": None,
    "ganador": None,
    "ganador_nombre": None,
    "lobby": [],
}


def obtener_ip_local():
    socket_temporal = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        socket_temporal.connect(("8.8.8.8", 80))
        ip = socket_temporal.getsockname()[0]
    except OSError:
        ip = "127.0.0.1"
    socket_temporal.close()
    return ip


def obtener_broadcast_de_subred():
    ip_local = obtener_ip_local()
    partes = ip_local.split(".")

    if len(partes) != 4:
        return None

    return partes[0] + "." + partes[1] + "." + partes[2] + ".255"


def leer_server_info(datos, ip_origen):
    if not datos.endswith(b"\n"):
        datos = datos + b"\n"

    lector = p.LectorMensajes()
    mensajes = lector.agregar_bytes(datos)

    for mensaje in mensajes:
        if mensaje.get("type") == "server_info":
            return {
                "ip": ip_origen,
                "tcp_port": mensaje.get("tcp_port", PUERTO_DEFECTO),
                "name": mensaje.get("name", "Servidor sin nombre"),
                "state": mensaje.get("state", "?"),
                "players": mensaje.get("players", "?"),
            }

    return None


def descubrir_servidores(segundos_espera=2):
    servidores = []

    socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    socket_udp.settimeout(0.3)

    mensaje_discover = {"type": "discover", "v": 1}
    texto_discover = json.dumps(mensaje_discover)
    datos_discover = texto_discover.encode("utf-8")

    destinos = ["255.255.255.255"]
    broadcast_subred = obtener_broadcast_de_subred()
    if broadcast_subred is not None:
        destinos.append(broadcast_subred)

    for destino in destinos:
        try:
            registro.log_json_enviado(texto_discover)
            socket_udp.sendto(datos_discover, (destino, 8888))
        except OSError:
            registro.log_error("No se pudo enviar el discover a", destino)

    momento_final = time.time() + segundos_espera

    while time.time() < momento_final:
        try:
            datos, direccion_servidor = socket_udp.recvfrom(1024)
        except socket.timeout:
            continue

        servidor = leer_server_info(datos, direccion_servidor[0])

        if servidor is None:
            continue

        ya_existe = False
        for existente in servidores:
            if existente["ip"] == servidor["ip"] and existente["tcp_port"] == servidor["tcp_port"]:
                ya_existe = True

        if not ya_existe:
            servidores.append(servidor)
            registro.log_evento("Servidor encontrado:", servidor["name"], "en", servidor["ip"])

    socket_udp.close()
    return servidores


def preguntar_puerto_por_unicast(ip, segundos_espera=2):
    socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_udp.settimeout(segundos_espera)

    mensaje_discover = {"type": "discover", "v": 1}
    texto_discover = json.dumps(mensaje_discover)

    puerto_encontrado = None

    try:
        registro.log_json_enviado(texto_discover)
        socket_udp.sendto(texto_discover.encode("utf-8"), (ip, 8888))
        datos, direccion_servidor = socket_udp.recvfrom(1024)
        servidor = leer_server_info(datos, direccion_servidor[0])
        if servidor is not None:
            puerto_encontrado = servidor["tcp_port"]
    except (socket.timeout, OSError):
        registro.log_error("El servidor", ip, "no respondio al discover directo")
        puerto_encontrado = None

    socket_udp.close()
    return puerto_encontrado


def conectar_manual(texto_escrito, nombre):
    ip = texto_escrito.strip()
    puerto = None

    if ":" in ip:
        partes = ip.split(":")
        ip = partes[0]
        try:
            puerto = int(partes[1])
        except ValueError:
            puerto = None

    if puerto is None:
        puerto = preguntar_puerto_por_unicast(ip)

    if puerto is None:
        puerto = PUERTO_DEFECTO

    return conectar(ip, puerto, nombre)


def conectar(ip, puerto, nombre):
    global conexion_servidor

    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.settimeout(5)
        cliente.connect((ip, puerto))
        cliente.settimeout(None)
    except OSError as error:
        estado_cliente["error"] = "No se pudo conectar: " + str(error)
        registro.log_error("Fallo la conexion a", ip, puerto, "-", error)
        return False

    conexion_servidor = cliente
    estado_cliente["conectado"] = True
    estado_cliente["error"] = None
    estado_cliente["mi_nombre"] = nombre
    estado_cliente["fase"] = "lobby"
    registro.log_evento("Conectado a", ip, "puerto", puerto)

    mensaje_join = {
        "type": "join",
        "v": 1,
        "name": nombre,
    }
    p.enviar(cliente, mensaje_join)

    hilo = threading.Thread(target=escuchar_mensajes)
    hilo.daemon = True
    hilo.start()

    return True


def escuchar_mensajes():
    lector = p.LectorMensajes()

    try:
        while True:
            datos_recibidos = conexion_servidor.recv(1024)

            if not datos_recibidos:
                break

            mensajes = lector.agregar_bytes(datos_recibidos)

            if lector.hubo_json_invalido:
                lector.hubo_json_invalido = False
                registro.log_error("El servidor mando un JSON invalido")

            for mensaje in mensajes:
                tipo = mensaje.get("type")

                if tipo == "welcome":
                    config_juego["map_size"] = mensaje["config"]["map_size"]
                    config_juego["circle_radius"] = mensaje["config"]["circle_radius"]
                    config_juego["player_radius"] = mensaje["config"].get("player_radius", 15)
                    estado_cliente["mi_id"] = mensaje["player_id"]
                    registro.log_evento("Soy el jugador", mensaje["player_id"])

                if tipo == "lobby":
                    estado_cliente["lobby"] = mensaje.get("players", [])
                    estado_cliente["fase"] = "lobby"
                    estado_cliente["countdown"] = None
                    estado_cliente["ganador"] = None
                    estado_cliente["ganador_nombre"] = None

                if tipo == "state":
                    ultimo_state["players"] = mensaje["players"]
                    ultimo_state["flag"] = mensaje["flag"]

                if tipo == "countdown":
                    estado_cliente["fase"] = "countdown"
                    estado_cliente["countdown"] = mensaje.get("seconds")

                if tipo == "start":
                    estado_cliente["fase"] = "playing"
                    estado_cliente["countdown"] = None
                    registro.log_evento("La partida ha comenzado")

                if tipo == "game_over":
                    estado_cliente["fase"] = "finished"
                    estado_cliente["ganador"] = mensaje.get("winner")
                    estado_cliente["ganador_nombre"] = mensaje.get("winner_name")
                    registro.log_evento("Fin de partida, gano", mensaje.get("winner"))

                if tipo == "error":
                    registro.log_error("El servidor rechazo algo:", mensaje.get("reason"))
    except (ConnectionResetError, OSError):
        pass

    estado_cliente["conectado"] = False
    registro.log_evento("Se cerro la conexion con el servidor")


def enviar_input(direccion_x, direccion_y):
    if conexion_servidor is None:
        return
    if estado_cliente["fase"] != "playing":
        return

    mensaje = {"type": "input", "dir": {"x": direccion_x, "y": direccion_y}}
    try:
        p.enviar(conexion_servidor, mensaje)
    except (ConnectionResetError, OSError):
        registro.log_error("No se pudo enviar el input")


def enviar_interact():
    if conexion_servidor is None:
        return
    if estado_cliente["fase"] != "playing":
        return

    try:
        p.enviar(conexion_servidor, {"type": "interact"})
    except (ConnectionResetError, OSError):
        registro.log_error("No se pudo enviar el interact")