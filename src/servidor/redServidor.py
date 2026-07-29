# src/servidor/redServidor.py

import socket
import threading
import json

from src.comun import protocolo as p
from src.comun import registro
from src.comun.constantes import CONFIG_DEFAULT, MAX_JUGADORES, NOMBRE_MAXIMO
from src.servidor import estado_partida as estado
from src.servidor import fisica
from src.servidor import ciclo_partida

PUERTO_JUEGO = 8889


def procesar_join(conexion, id_jugador, mensaje):
    if id_jugador in estado.jugadores_conectados:
        estado.enviar_error(conexion, "INVALID_PHASE")
        return False

    if estado.fase_partida != "lobby":
        estado.enviar_error(conexion, "GAME_STARTED")
        registro.log_error("Join rechazado de", id_jugador, "- la partida ya inicio")
        return True

    version_cliente = mensaje.get("v")

    if version_cliente is not None and version_cliente != 1:
        estado.enviar_error(conexion, "VERSION_MISMATCH")
        registro.log_error("Join rechazado de", id_jugador, "- version", version_cliente)
        return True

    if estado.cantidad_jugadores() >= MAX_JUGADORES:
        estado.enviar_error(conexion, "LOBBY_FULL")
        registro.log_error("Join rechazado de", id_jugador, "- lobby lleno")
        return True

    if "name" not in mensaje:
        estado.enviar_error(conexion, "MISSING_FIELD")
        registro.log_error("Join sin campo name de", id_jugador)
        return False

    if not isinstance(mensaje["name"], str):
        estado.enviar_error(conexion, "INVALID_FIELD")
        registro.log_error("Join con name invalido de", id_jugador)
        return False

    nombre_limpio = mensaje["name"].strip()

    if nombre_limpio == "" or len(nombre_limpio) > NOMBRE_MAXIMO:
        estado.enviar_error(conexion, "NAME_INVALID")
        registro.log_error("Join con nombre fuera de rango de", id_jugador)
        return False

    estado.agregar_jugador(id_jugador, nombre_limpio, conexion)
    registro.log_evento(nombre_limpio, "entro al lobby como", id_jugador)

    respuesta = {
        "type": "welcome",
        "player_id": id_jugador,
        "config": CONFIG_DEFAULT,
    }
    p.enviar(conexion, respuesta)

    estado.enviar_lobby_a_todos()
    return False


def procesar_input(conexion, id_jugador, mensaje):
    if id_jugador not in estado.jugadores_conectados:
        estado.enviar_error(conexion, "NOT_JOINED")
        return

    if estado.fase_partida != "playing":
        estado.enviar_error(conexion, "INVALID_PHASE")
        return

    if "dir" not in mensaje or not isinstance(mensaje["dir"], dict):
        estado.enviar_error(conexion, "MISSING_FIELD")
        return

    dir_x = mensaje["dir"].get("x")
    dir_y = mensaje["dir"].get("y")

    if not isinstance(dir_x, int) or not isinstance(dir_y, int):
        estado.enviar_error(conexion, "INVALID_FIELD")
        return

    if dir_x < -1 or dir_x > 1 or dir_y < -1 or dir_y > 1:
        estado.enviar_error(conexion, "INVALID_FIELD")
        return

    estado.jugadores_conectados[id_jugador]["dir_x"] = dir_x
    estado.jugadores_conectados[id_jugador]["dir_y"] = dir_y


def procesar_interact(conexion, id_jugador):
    if id_jugador not in estado.jugadores_conectados:
        estado.enviar_error(conexion, "NOT_JOINED")
        return

    if estado.fase_partida != "playing":
        estado.enviar_error(conexion, "INVALID_PHASE")
        return

    datos_jugador = estado.jugadores_conectados[id_jugador]
    distancia = fisica.calcular_distancia(
        datos_jugador["x"], datos_jugador["y"],
        estado.bandera["x"], estado.bandera["y"]
    )

    if distancia > CONFIG_DEFAULT["interact_radius"]:
        return

    if estado.bandera["owner"] == id_jugador:
        return

    era_libre = estado.bandera["owner"] is None

    estado.bandera["owner"] = id_jugador
    estado.bandera["puede_ganar"] = fisica.esta_dentro_del_circulo(datos_jugador["x"], datos_jugador["y"])

    if era_libre:
        registro.log_evento(datos_jugador["nombre"], "tomo la bandera")
    else:
        registro.log_evento(datos_jugador["nombre"], "robo la bandera")


def procesar_mensaje(conexion, id_jugador, mensaje):
    tipo_mensaje = mensaje.get("type")

    if tipo_mensaje == "join":
        return procesar_join(conexion, id_jugador, mensaje)

    if tipo_mensaje == "input":
        procesar_input(conexion, id_jugador, mensaje)
        return False

    if tipo_mensaje == "interact":
        procesar_interact(conexion, id_jugador)
        return False

    estado.enviar_error(conexion, "UNKNOWN_TYPE")
    registro.log_error("Tipo desconocido de", id_jugador, ":", tipo_mensaje)
    return False


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
                estado.enviar_error(conexion, "MESSAGE_TOO_LARGE")
                registro.log_error("Mensaje demasiado grande de", id_jugador)
                break

            if lector.hubo_json_invalido:
                lector.hubo_json_invalido = False
                estado.enviar_error(conexion, "INVALID_JSON")
                registro.log_error("JSON invalido de", id_jugador)

            for mensaje in mensajes:
                cerrar_conexion = procesar_mensaje(conexion, id_jugador, mensaje)

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

    estado.desconectar_jugador(id_jugador)


def responder_discover(socket_udp, direccion_cliente):
    respuesta = {
        "type": "server_info",
        "v": 1,
        "name": "Servidor CTF Nav",
        "tcp_port": PUERTO_JUEGO,
        "state": estado.estado_para_descubrimiento(),
        "players": estado.cantidad_jugadores(),
    }

    texto_respuesta = json.dumps(respuesta)
    registro.log_json_enviado(texto_respuesta)
    socket_udp.sendto(texto_respuesta.encode("utf-8"), direccion_cliente)
    registro.log_evento("Respondi a un discover desde", direccion_cliente[0])


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

            responder_discover(socket_udp, direccion_cliente)


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


def arrancar_hilo(funcion, argumentos=()):
    hilo = threading.Thread(target=funcion, args=argumentos)
    hilo.daemon = True
    hilo.start()


def iniciar_servidor_en_hilos():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(("0.0.0.0", PUERTO_JUEGO))
    servidor.listen()
    registro.log_evento("Servidor esperando conexiones en el puerto", PUERTO_JUEGO)

    arrancar_hilo(ciclo_partida.ciclo_de_estado)
    arrancar_hilo(escuchar_descubrimiento)
    arrancar_hilo(aceptar_conexiones, (servidor,))