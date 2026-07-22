import socket
import threading
import time
import random
import math
import json
from src.comun import protocolo as p
from src.comun.constantes import CONFIG_DEFAULT, COUNTDOWN_SEGUNDOS, MAX_JUGADORES, NOMBRE_MAXIMO

PUERTO_JUEGO = 8889

jugadores_conectados = {}
bandera = {"owner": None, "x": 500, "y": 500}
juego_terminado = False
fase_partida = "lobby"
id_ganador = None


def generar_posicion_inicial():
    centro = CONFIG_DEFAULT["map_size"] / 2
    radio_circulo = CONFIG_DEFAULT["circle_radius"]

    while True:
        x = random.uniform(0, CONFIG_DEFAULT["map_size"])
        y = random.uniform(0, CONFIG_DEFAULT["map_size"])
        distancia_al_centro = math.sqrt((x - centro) ** 2 + (y - centro) ** 2)
        if distancia_al_centro > radio_circulo:
            return x, y


def calcular_distancia(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def enviar_lobby_a_todos():
    lista_jugadores = []
    for id_jugador in jugadores_conectados:
        nombre = jugadores_conectados[id_jugador]["nombre"]
        lista_jugadores.append({"id": id_jugador, "name": nombre})

    mensaje_lobby = {
        "type": "lobby",
        "players": lista_jugadores,
    }

    enviar_a_todos(mensaje_lobby)


def enviar_a_todos(mensaje):
    for id_jugador in jugadores_conectados:
        conexion_jugador = jugadores_conectados[id_jugador]["conexion"]
        try:
            p.enviar(conexion_jugador, mensaje)
        except (ConnectionResetError, OSError):
            pass


def iniciar_countdown():
    global fase_partida

    if fase_partida != "lobby":
        return

    fase_partida = "countdown"
    segundos_restantes = COUNTDOWN_SEGUNDOS

    while segundos_restantes > 0:
        mensaje_countdown = {
            "type": "countdown",
            "seconds": segundos_restantes,
        }
        enviar_a_todos(mensaje_countdown)
        print("Countdown:", segundos_restantes)
        time.sleep(1)
        segundos_restantes = segundos_restantes - 1

    fase_partida = "playing"
    mensaje_start = {"type": "start"}
    enviar_a_todos(mensaje_start)
    print("La partida ha iniciado")


def mover_jugador(datos_jugador, segundos_transcurridos):
    velocidad = CONFIG_DEFAULT["speed"]
    limite_mapa = CONFIG_DEFAULT["map_size"]
    radio_jugador = CONFIG_DEFAULT["player_radius"]

    nueva_x = datos_jugador["x"] + datos_jugador["dir_x"] * velocidad * segundos_transcurridos
    nueva_y = datos_jugador["y"] + datos_jugador["dir_y"] * velocidad * segundos_transcurridos

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


def ciclo_de_estado():
    global juego_terminado, id_ganador
    tick_rate = CONFIG_DEFAULT["tick_rate"]
    segundos_entre_ticks = 1 / tick_rate

    while True:
        time.sleep(segundos_entre_ticks)

        if fase_partida == "playing" and not juego_terminado:
            for id_jugador in jugadores_conectados:
                datos_jugador = jugadores_conectados[id_jugador]
                mover_jugador(datos_jugador, segundos_entre_ticks)

            if bandera["owner"] is not None:
                if bandera["owner"] in jugadores_conectados:
                    jugador_portador = jugadores_conectados[bandera["owner"]]
                    bandera["x"] = jugador_portador["x"]
                    bandera["y"] = jugador_portador["y"]

            if bandera["owner"] is not None:
                centro = CONFIG_DEFAULT["map_size"] / 2
                radio_limite = CONFIG_DEFAULT["circle_radius"] + CONFIG_DEFAULT["player_radius"]
                distancia_al_centro = calcular_distancia(bandera["x"], bandera["y"], centro, centro)

                if distancia_al_centro > radio_limite:
                    juego_terminado = True
                    id_ganador = bandera["owner"]
                    mensaje_ganador = {
                        "type": "game_over",
                        "winner": bandera["owner"],
                    }
                    enviar_a_todos(mensaje_ganador)
                    print(bandera["owner"], "gano la partida")

        if not juego_terminado:
            lista_jugadores = []
            for id_jugador in jugadores_conectados:
                datos_jugador = jugadores_conectados[id_jugador]
                lista_jugadores.append({
                    "id": id_jugador,
                    "x": datos_jugador["x"],
                    "y": datos_jugador["y"],
                })

            mensaje_state = {
                "type": "state",
                "flag": {"owner": bandera["owner"], "x": bandera["x"], "y": bandera["y"]},
                "players": lista_jugadores,
            }

            enviar_a_todos(mensaje_state)


def desconectar_jugador(id_jugador):
    if id_jugador in jugadores_conectados:
        del jugadores_conectados[id_jugador]
        print(id_jugador, "se desconecto")

        if bandera["owner"] == id_jugador:
            bandera["owner"] = None
            bandera["x"] = CONFIG_DEFAULT["map_size"] / 2
            bandera["y"] = CONFIG_DEFAULT["map_size"] / 2
            print("La bandera volvio al centro porque el portador se desconecto")


def atender_cliente(conexion, direccion, id_jugador):
    lector = p.LectorMensajes()

    try:
        while True:
            datos_recibidos = conexion.recv(1024)

            if not datos_recibidos:
                break

            mensajes = lector.agregar_bytes(datos_recibidos)

            for mensaje in mensajes:
                print("Mensaje recibido de", id_jugador, ":", mensaje)

                tipo_mensaje = mensaje.get("type")

                if tipo_mensaje == "join":
                    if fase_partida != "lobby":
                        mensaje_error = {
                            "type": "error",
                            "reason": "game_started",
                        }
                        p.enviar(conexion, mensaje_error)
                        print("Se rechazo el join de", id_jugador, "porque la partida ya inicio")
                        continue

                    if len(jugadores_conectados) >= MAX_JUGADORES:
                        mensaje_error = {
                            "type": "error",
                            "reason": "lobby_full",
                        }
                        p.enviar(conexion, mensaje_error)
                        print("Se rechazo el join de", id_jugador, "porque el lobby esta lleno")
                        continue

                    if "name" not in mensaje:
                        mensaje_error = {
                            "type": "error",
                            "reason": "missing_field",
                        }
                        p.enviar(conexion, mensaje_error)
                        continue

                    if not isinstance(mensaje["name"], str):
                        mensaje_error = {
                            "type": "error",
                            "reason": "invalid_field",
                        }
                        p.enviar(conexion, mensaje_error)
                        continue

                    nombre_limpio = mensaje["name"].strip()

                    if nombre_limpio == "" or len(nombre_limpio) > NOMBRE_MAXIMO:
                        mensaje_error = {
                            "type": "error",
                            "reason": "name_invalid",
                        }
                        p.enviar(conexion, mensaje_error)
                        continue

                    x_inicial, y_inicial = generar_posicion_inicial()
                    jugadores_conectados[id_jugador] = {
                        "nombre": nombre_limpio,
                        "conexion": conexion,
                        "x": x_inicial,
                        "y": y_inicial,
                        "dir_x": 0,
                        "dir_y": 0,
                    }
                    print("Jugadores conectados ahora:", list(jugadores_conectados.keys()))

                    respuesta = {
                        "type": "welcome",
                        "player_id": id_jugador,
                        "config": CONFIG_DEFAULT,
                    }
                    p.enviar(conexion, respuesta)

                    enviar_lobby_a_todos()

                if tipo_mensaje == "input":
                    if id_jugador not in jugadores_conectados:
                        mensaje_error = {
                            "type": "error",
                            "reason": "not_joined",
                        }
                        p.enviar(conexion, mensaje_error)
                        continue

                    if "dir" not in mensaje or not isinstance(mensaje["dir"], dict):
                        mensaje_error = {
                            "type": "error",
                            "reason": "missing_field",
                        }
                        p.enviar(conexion, mensaje_error)
                        continue

                    dir_x = mensaje["dir"].get("x")
                    dir_y = mensaje["dir"].get("y")

                    if dir_x not in (-1, 0, 1) or dir_y not in (-1, 0, 1):
                        mensaje_error = {
                            "type": "error",
                            "reason": "invalid_field",
                        }
                        p.enviar(conexion, mensaje_error)
                        continue

                    jugadores_conectados[id_jugador]["dir_x"] = dir_x
                    jugadores_conectados[id_jugador]["dir_y"] = dir_y

                if tipo_mensaje == "interact":
                    if id_jugador not in jugadores_conectados:
                        mensaje_error = {
                            "type": "error",
                            "reason": "not_joined",
                        }
                        p.enviar(conexion, mensaje_error)
                        continue

                    datos_jugador = jugadores_conectados[id_jugador]
                    distancia = calcular_distancia(
                        datos_jugador["x"], datos_jugador["y"],
                        bandera["x"], bandera["y"]
                    )

                    if distancia <= CONFIG_DEFAULT["interact_radius"]:
                        if bandera["owner"] is None:
                            bandera["owner"] = id_jugador
                            print(id_jugador, "tomo la bandera")
                        elif bandera["owner"] != id_jugador:
                            bandera["owner"] = id_jugador
                            print(id_jugador, "robo la bandera")

    except (ConnectionResetError, OSError):
        pass

    desconectar_jugador(id_jugador)


def escuchar_descubrimiento():
    socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socket_udp.bind(("0.0.0.0", 8888))
    print("Escuchando descubrimiento en el puerto UDP 8888")

    lector = p.LectorMensajes()

    while True:
        datos, direccion_cliente = socket_udp.recvfrom(1024)

        if not datos.endswith(b"\n"):
            datos = datos + b"\n"

        mensajes = lector.agregar_bytes(datos)

        for mensaje in mensajes:
            if mensaje.get("type") == "discover":
                respuesta = {
                    "type": "server_info",
                    "v": 1,
                    "name": "Servidor CTF",
                    "tcp_port": PUERTO_JUEGO,
                    "state": fase_partida,
                    "players": len(jugadores_conectados),
                }
                texto_respuesta = json.dumps(respuesta) + "\n"
                socket_udp.sendto(texto_respuesta.encode("utf-8"), direccion_cliente)
                print("Respondi a un discover desde", direccion_cliente)


def aceptar_conexiones(servidor):
    contador_jugadores = 0

    while True:
        conexion, direccion = servidor.accept()
        contador_jugadores = contador_jugadores + 1
        id_jugador = "p" + str(contador_jugadores)
        print("Se conecto un cliente desde", direccion, "- asignado como", id_jugador)

        hilo = threading.Thread(target=atender_cliente, args=(conexion, direccion, id_jugador))
        hilo.daemon = True
        hilo.start()


def iniciar_servidor_en_hilos():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(("0.0.0.0", PUERTO_JUEGO))
    servidor.listen()
    print("Servidor esperando conexiones en el puerto", PUERTO_JUEGO)

    hilo_estado = threading.Thread(target=ciclo_de_estado)
    hilo_estado.daemon = True
    hilo_estado.start()

    hilo_descubrimiento = threading.Thread(target=escuchar_descubrimiento)
    hilo_descubrimiento.daemon = True
    hilo_descubrimiento.start()

    hilo_conexiones = threading.Thread(target=aceptar_conexiones, args=(servidor,))
    hilo_conexiones.daemon = True
    hilo_conexiones.start()