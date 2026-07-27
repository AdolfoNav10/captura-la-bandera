import socket
import threading
import time
import random
import math
import json
from src.comun import protocolo as p
from src.comun import registro
from src.comun.constantes import (
    CONFIG_DEFAULT,
    COUNTDOWN_SEGUNDOS,
    MIN_JUGADORES,
    POST_GAME_SEGUNDOS,
    SPAWN_RADIO_MIN,
    SPAWN_RADIO_MAX,
    MAX_JUGADORES,
    NOMBRE_MAXIMO,
)

PUERTO_JUEGO = 8889

jugadores_conectados = {}
bandera = {"owner": None, "x": 500, "y": 500, "puede_ganar": False}
juego_terminado = False
fase_partida = "lobby"

id_ganador = None
nombre_ganador = None
countdown_actual = None


def generar_posicion_inicial():
    centro = CONFIG_DEFAULT["map_size"] / 2
    angulo = random.uniform(0, 2 * math.pi)
    radio = random.uniform(SPAWN_RADIO_MIN, SPAWN_RADIO_MAX)
    x = centro + radio * math.cos(angulo)
    y = centro + radio * math.sin(angulo)
    return x, y


def calcular_distancia(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def estado_para_descubrimiento():
    if fase_partida == "lobby":
        return "lobby"
    return "playing"


def enviar_error(conexion, codigo):
    mensaje_error = {"type": "error", "reason": codigo}
    try:
        p.enviar(conexion, mensaje_error)
    except (ConnectionResetError, OSError):
        pass


def enviar_a_todos(mensaje):
    for id_jugador in list(jugadores_conectados.keys()):
        if id_jugador in jugadores_conectados:
            conexion_jugador = jugadores_conectados[id_jugador]["conexion"]
            try:
                p.enviar(conexion_jugador, mensaje)
            except (ConnectionResetError, OSError):
                pass


def enviar_lobby_a_todos():
    lista_jugadores = []
    for id_jugador in list(jugadores_conectados.keys()):
        if id_jugador in jugadores_conectados:
            nombre = jugadores_conectados[id_jugador]["nombre"]
            lista_jugadores.append({"id": id_jugador, "name": nombre})

    mensaje_lobby = {
        "type": "lobby",
        "players": lista_jugadores,
    }

    enviar_a_todos(mensaje_lobby)


def colocar_jugadores_en_spawn():
    for id_jugador in list(jugadores_conectados.keys()):
        if id_jugador in jugadores_conectados:
            x_inicial, y_inicial = generar_posicion_inicial()
            jugadores_conectados[id_jugador]["x"] = x_inicial
            jugadores_conectados[id_jugador]["y"] = y_inicial
            jugadores_conectados[id_jugador]["dir_x"] = 0
            jugadores_conectados[id_jugador]["dir_y"] = 0

    bandera["owner"] = None
    bandera["x"] = CONFIG_DEFAULT["map_size"] / 2
    bandera["y"] = CONFIG_DEFAULT["map_size"] / 2
    bandera["puede_ganar"] = False


def iniciar_countdown():
    global fase_partida, countdown_actual

    if fase_partida != "lobby":
        return

    if len(jugadores_conectados) < MIN_JUGADORES:
        registro.log_evento("Se necesitan al menos", MIN_JUGADORES, "jugadores para iniciar")
        return

    fase_partida = "countdown"
    segundos_restantes = COUNTDOWN_SEGUNDOS

    while segundos_restantes > 0:
        if len(jugadores_conectados) < MIN_JUGADORES:
            registro.log_evento("Countdown cancelado: quedan menos de", MIN_JUGADORES, "jugadores")
            countdown_actual = None
            fase_partida = "lobby"
            enviar_lobby_a_todos()
            return

        countdown_actual = segundos_restantes
        mensaje_countdown = {
            "type": "countdown",
            "seconds": segundos_restantes,
        }
        enviar_a_todos(mensaje_countdown)
        registro.log_evento("Countdown:", segundos_restantes)
        time.sleep(1)
        segundos_restantes = segundos_restantes - 1

    countdown_actual = None
    colocar_jugadores_en_spawn()

    enviar_a_todos({"type": "start"})
    fase_partida = "playing"
    registro.log_evento("La partida ha iniciado")


def terminar_partida(id_del_ganador):
    global juego_terminado, id_ganador, nombre_ganador, fase_partida

    juego_terminado = True
    fase_partida = "finished"
    id_ganador = id_del_ganador
    nombre_ganador = jugadores_conectados[id_del_ganador]["nombre"]

    mensaje_ganador = {
        "type": "game_over",
        "winner": id_del_ganador,
        "winner_name": nombre_ganador,
    }
    enviar_a_todos(mensaje_ganador)
    registro.log_evento(nombre_ganador, "gano la partida")

    hilo = threading.Thread(target=volver_al_lobby)
    hilo.daemon = True
    hilo.start()


def volver_al_lobby():
    global juego_terminado, id_ganador, nombre_ganador, fase_partida

    time.sleep(POST_GAME_SEGUNDOS)

    juego_terminado = False
    id_ganador = None
    nombre_ganador = None

    bandera["owner"] = None
    bandera["x"] = CONFIG_DEFAULT["map_size"] / 2
    bandera["y"] = CONFIG_DEFAULT["map_size"] / 2
    bandera["puede_ganar"] = False

    fase_partida = "lobby"
    enviar_lobby_a_todos()
    registro.log_evento("De vuelta en el lobby")


def mover_jugador(datos_jugador, segundos_transcurridos):
    velocidad = CONFIG_DEFAULT["speed"]
    limite_mapa = CONFIG_DEFAULT["map_size"]
    radio_jugador = CONFIG_DEFAULT["player_radius"]

    dir_x = datos_jugador["dir_x"]
    dir_y = datos_jugador["dir_y"]

    if dir_x != 0 and dir_y != 0:
        factor = math.sqrt(2)
        dir_x = dir_x / factor
        dir_y = dir_y / factor

    nueva_x = datos_jugador["x"] + dir_x * velocidad * segundos_transcurridos
    nueva_y = datos_jugador["y"] + dir_y * velocidad * segundos_transcurridos

    if nueva_x < radio_jugador:
        nueva_x = radio_jugador
    if nueva_x > limite_mapa - radio_jugador:
        nueva_x = limite_mapa - radio_jugador

    if nueva_y < radio_jugador:
        nueva_y = radio_jugador
    if nueva_y > limite_mapa - radio_jugador:
        nueva_y = limite_mapa - radio_jugador

    datos_jugador["x"] = nueva_x
    datos_jugador["y"] = nueva_y


def marcar_si_puede_ganar(id_jugador):
    datos_jugador = jugadores_conectados[id_jugador]
    centro = CONFIG_DEFAULT["map_size"] / 2
    limite = CONFIG_DEFAULT["circle_radius"] + CONFIG_DEFAULT["player_radius"]
    distancia_al_centro = calcular_distancia(datos_jugador["x"], datos_jugador["y"], centro, centro)

    if distancia_al_centro <= limite:
        bandera["puede_ganar"] = True
    else:
        bandera["puede_ganar"] = False


def enviar_state_a_todos():
    lista_jugadores = []
    for id_jugador in list(jugadores_conectados.keys()):
        if id_jugador in jugadores_conectados:
            datos_jugador = jugadores_conectados[id_jugador]
            lista_jugadores.append({
                "id": id_jugador,
                "x": round(datos_jugador["x"], 1),
                "y": round(datos_jugador["y"], 1),
            })

    mensaje_state = {
        "type": "state",
        "flag": {
            "owner": bandera["owner"],
            "x": round(bandera["x"], 1),
            "y": round(bandera["y"], 1),
        },
        "players": lista_jugadores,
    }

    enviar_a_todos(mensaje_state)


def ciclo_de_estado():
    tick_rate = CONFIG_DEFAULT["tick_rate"]
    segundos_entre_ticks = 1 / tick_rate

    while True:
        time.sleep(segundos_entre_ticks)

        if fase_partida != "playing":
            continue

        for id_jugador in list(jugadores_conectados.keys()):
            if id_jugador in jugadores_conectados:
                datos_jugador = jugadores_conectados[id_jugador]
                mover_jugador(datos_jugador, segundos_entre_ticks)

        if bandera["owner"] is not None and bandera["owner"] in jugadores_conectados:
            jugador_portador = jugadores_conectados[bandera["owner"]]
            bandera["x"] = jugador_portador["x"]
            bandera["y"] = jugador_portador["y"]

            centro = CONFIG_DEFAULT["map_size"] / 2
            limite = CONFIG_DEFAULT["circle_radius"] + CONFIG_DEFAULT["player_radius"]
            distancia_al_centro = calcular_distancia(bandera["x"], bandera["y"], centro, centro)

            if not bandera["puede_ganar"] and distancia_al_centro <= limite:
                bandera["puede_ganar"] = True

            if bandera["puede_ganar"] and distancia_al_centro > limite:
                terminar_partida(bandera["owner"])
                continue

        enviar_state_a_todos()


def desconectar_jugador(id_jugador):
    global fase_partida, juego_terminado, id_ganador, nombre_ganador

    if id_jugador not in jugadores_conectados:
        return

    nombre = jugadores_conectados[id_jugador]["nombre"]
    del jugadores_conectados[id_jugador]
    registro.log_evento(nombre, "(" + id_jugador + ") se desconecto")

    if bandera["owner"] == id_jugador:
        bandera["owner"] = None
        bandera["x"] = CONFIG_DEFAULT["map_size"] / 2
        bandera["y"] = CONFIG_DEFAULT["map_size"] / 2
        bandera["puede_ganar"] = False
        registro.log_evento("La bandera volvio al centro")

    if fase_partida == "lobby":
        enviar_lobby_a_todos()
        return

    if len(jugadores_conectados) == 0:
        juego_terminado = False
        id_ganador = None
        nombre_ganador = None
        fase_partida = "lobby"
        registro.log_evento("No quedan jugadores, de vuelta al lobby")


def procesar_join(conexion, id_jugador, mensaje):
    if id_jugador in jugadores_conectados:
        enviar_error(conexion, "INVALID_PHASE")
        return False

    if fase_partida != "lobby":
        enviar_error(conexion, "GAME_STARTED")
        registro.log_error("Join rechazado de", id_jugador, "- la partida ya inicio")
        return True

    version_cliente = mensaje.get("v")
    if version_cliente is not None and version_cliente != 1:
        enviar_error(conexion, "VERSION_MISMATCH")
        registro.log_error("Join rechazado de", id_jugador, "- version", version_cliente)
        return True

    if len(jugadores_conectados) >= MAX_JUGADORES:
        enviar_error(conexion, "LOBBY_FULL")
        registro.log_error("Join rechazado de", id_jugador, "- lobby lleno")
        return True

    if "name" not in mensaje:
        enviar_error(conexion, "MISSING_FIELD")
        registro.log_error("Join sin campo name de", id_jugador)
        return False

    if not isinstance(mensaje["name"], str):
        enviar_error(conexion, "INVALID_FIELD")
        registro.log_error("Join con name invalido de", id_jugador)
        return False

    nombre_limpio = mensaje["name"].strip()

    if nombre_limpio == "" or len(nombre_limpio) > NOMBRE_MAXIMO:
        enviar_error(conexion, "NAME_INVALID")
        registro.log_error("Join con nombre fuera de rango de", id_jugador)
        return False

    x_inicial, y_inicial = generar_posicion_inicial()
    jugadores_conectados[id_jugador] = {
        "nombre": nombre_limpio,
        "conexion": conexion,
        "x": x_inicial,
        "y": y_inicial,
        "dir_x": 0,
        "dir_y": 0,
    }
    registro.log_evento(nombre_limpio, "entro al lobby como", id_jugador)

    respuesta = {
        "type": "welcome",
        "player_id": id_jugador,
        "config": CONFIG_DEFAULT,
    }
    p.enviar(conexion, respuesta)

    enviar_lobby_a_todos()
    return False


def procesar_input(conexion, id_jugador, mensaje):
    if id_jugador not in jugadores_conectados:
        enviar_error(conexion, "NOT_JOINED")
        return

    if fase_partida != "playing":
        enviar_error(conexion, "INVALID_PHASE")
        return

    if "dir" not in mensaje or not isinstance(mensaje["dir"], dict):
        enviar_error(conexion, "MISSING_FIELD")
        return

    dir_x = mensaje["dir"].get("x")
    dir_y = mensaje["dir"].get("y")

    if not isinstance(dir_x, int) or not isinstance(dir_y, int):
        enviar_error(conexion, "INVALID_FIELD")
        return

    if dir_x < -1 or dir_x > 1 or dir_y < -1 or dir_y > 1:
        enviar_error(conexion, "INVALID_FIELD")
        return

    jugadores_conectados[id_jugador]["dir_x"] = dir_x
    jugadores_conectados[id_jugador]["dir_y"] = dir_y


def procesar_interact(conexion, id_jugador):
    if id_jugador not in jugadores_conectados:
        enviar_error(conexion, "NOT_JOINED")
        return

    if fase_partida != "playing":
        enviar_error(conexion, "INVALID_PHASE")
        return

    datos_jugador = jugadores_conectados[id_jugador]
    distancia = calcular_distancia(
        datos_jugador["x"], datos_jugador["y"],
        bandera["x"], bandera["y"]
    )

    if distancia > CONFIG_DEFAULT["interact_radius"]:
        return

    if bandera["owner"] == id_jugador:
        return

    if bandera["owner"] is None:
        bandera["owner"] = id_jugador
        marcar_si_puede_ganar(id_jugador)
        registro.log_evento(datos_jugador["nombre"], "tomo la bandera")
    else:
        bandera["owner"] = id_jugador
        marcar_si_puede_ganar(id_jugador)
        registro.log_evento(datos_jugador["nombre"], "robo la bandera")


def atender_cliente(conexion, direccion, id_jugador):
    lector = p.LectorMensajes()
    cerrar_conexion = False

    try:
        while True:
            datos_recibidos = conexion.recv(1024)

            if not datos_recibidos:
                break

            mensajes = lector.agregar_bytes(datos_recibidos)

            if lector.mensaje_muy_grande:
                enviar_error(conexion, "MESSAGE_TOO_LARGE")
                registro.log_error("Mensaje demasiado grande de", id_jugador)
                break

            if lector.hubo_json_invalido:
                lector.hubo_json_invalido = False
                enviar_error(conexion, "INVALID_JSON")
                registro.log_error("JSON invalido de", id_jugador)

            for mensaje in mensajes:
                tipo_mensaje = mensaje.get("type")

                if tipo_mensaje == "join":
                    cerrar_conexion = procesar_join(conexion, id_jugador, mensaje)
                elif tipo_mensaje == "input":
                    procesar_input(conexion, id_jugador, mensaje)
                elif tipo_mensaje == "interact":
                    procesar_interact(conexion, id_jugador)
                else:
                    enviar_error(conexion, "UNKNOWN_TYPE")
                    registro.log_error("Tipo desconocido de", id_jugador, ":", tipo_mensaje)

                if cerrar_conexion:
                    break

            if cerrar_conexion:
                break

    except (ConnectionResetError, OSError):
        pass

    try:
        conexion.close()
    except OSError:
        pass

    desconectar_jugador(id_jugador)


def escuchar_descubrimiento():
    socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socket_udp.bind(("0.0.0.0", 8888))
    registro.log_evento("Escuchando descubrimiento en el puerto UDP 8888")

    while True:
        datos, direccion_cliente = socket_udp.recvfrom(1024)

        if not datos.endswith(b"\n"):
            datos = datos + b"\n"

        lector = p.LectorMensajes()
        mensajes = lector.agregar_bytes(datos)

        for mensaje in mensajes:
            if mensaje.get("type") != "discover":
                continue

            version_cliente = mensaje.get("v")
            if version_cliente is not None and version_cliente != 1:
                continue

            respuesta = {
                "type": "server_info",
                "v": 1,
                "name": "Servidor CTF",
                "tcp_port": PUERTO_JUEGO,
                "state": estado_para_descubrimiento(),
                "players": len(jugadores_conectados),
            }
            texto_respuesta = json.dumps(respuesta)
            registro.log_json_enviado(texto_respuesta)
            socket_udp.sendto(texto_respuesta.encode("utf-8"), direccion_cliente)
            registro.log_evento("Respondi a un discover desde", direccion_cliente[0])


def aceptar_conexiones(servidor):
    contador_jugadores = 0

    while True:
        conexion, direccion = servidor.accept()
        contador_jugadores = contador_jugadores + 1
        id_jugador = "p" + str(contador_jugadores)
        registro.log_evento("Conexion nueva desde", direccion[0], "- asignada como", id_jugador)

        hilo = threading.Thread(target=atender_cliente, args=(conexion, direccion, id_jugador))
        hilo.daemon = True
        hilo.start()


def iniciar_servidor_en_hilos():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(("0.0.0.0", PUERTO_JUEGO))
    servidor.listen()
    registro.log_evento("Servidor esperando conexiones en el puerto", PUERTO_JUEGO)

    hilo_estado = threading.Thread(target=ciclo_de_estado)
    hilo_estado.daemon = True
    hilo_estado.start()

    hilo_descubrimiento = threading.Thread(target=escuchar_descubrimiento)
    hilo_descubrimiento.daemon = True
    hilo_descubrimiento.start()

    hilo_conexiones = threading.Thread(target=aceptar_conexiones, args=(servidor,))
    hilo_conexiones.daemon = True
    hilo_conexiones.start()