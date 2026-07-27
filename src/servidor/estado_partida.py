# src/servidor/estado_partida.py

from src.comun import protocolo as p
from src.comun import registro
from src.servidor import fisica

jugadores_conectados = {}
bandera = {"owner": None, "x": 500, "y": 500, "puede_ganar": False}

fase_partida = "lobby"
juego_terminado = False
id_ganador = None
nombre_ganador = None
countdown_actual = None


def bandera_al_centro():
    centro = fisica.centro_del_mapa()
    bandera["owner"] = None
    bandera["x"] = centro
    bandera["y"] = centro
    bandera["puede_ganar"] = False


def ids_conectados():
    return list(jugadores_conectados.keys())


def cantidad_jugadores():
    return len(jugadores_conectados)


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
    for id_jugador in ids_conectados():
        if id_jugador in jugadores_conectados:
            conexion_jugador = jugadores_conectados[id_jugador]["conexion"]
            try:
                p.enviar(conexion_jugador, mensaje)
            except (ConnectionResetError, OSError):
                pass


def enviar_lobby_a_todos():
    lista_jugadores = []

    for id_jugador in ids_conectados():
        if id_jugador in jugadores_conectados:
            nombre = jugadores_conectados[id_jugador]["nombre"]
            lista_jugadores.append({"id": id_jugador, "name": nombre})

    mensaje_lobby = {
        "type": "lobby",
        "players": lista_jugadores,
    }

    enviar_a_todos(mensaje_lobby)


def agregar_jugador(id_jugador, nombre, conexion):
    x_inicial, y_inicial = fisica.generar_posicion_inicial()

    jugadores_conectados[id_jugador] = {
        "nombre": nombre,
        "conexion": conexion,
        "x": x_inicial,
        "y": y_inicial,
        "dir_x": 0,
        "dir_y": 0,
    }


def desconectar_jugador(id_jugador):
    global fase_partida, juego_terminado, id_ganador, nombre_ganador

    if id_jugador not in jugadores_conectados:
        return

    nombre = jugadores_conectados[id_jugador]["nombre"]
    del jugadores_conectados[id_jugador]
    registro.log_evento(nombre, "(" + id_jugador + ") se desconecto")

    if bandera["owner"] == id_jugador:
        bandera_al_centro()
        registro.log_evento("La bandera volvio al centro")

    if fase_partida == "lobby":
        enviar_lobby_a_todos()
        return

    if cantidad_jugadores() == 0:
        juego_terminado = False
        id_ganador = None
        nombre_ganador = None
        fase_partida = "lobby"
        registro.log_evento("No quedan jugadores, de vuelta al lobby")