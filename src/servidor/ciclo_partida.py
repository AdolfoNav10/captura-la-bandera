# src/servidor/ciclo_partida.py

import time
import threading

from src.comun import registro
from src.comun.constantes import CONFIG_DEFAULT, COUNTDOWN_SEGUNDOS, MIN_JUGADORES, POST_GAME_SEGUNDOS
from src.servidor import estado_partida as estado
from src.servidor import fisica


def colocar_jugadores_en_spawn():
    for id_jugador in estado.ids_conectados():
        if id_jugador in estado.jugadores_conectados:
            x_inicial, y_inicial = fisica.generar_posicion_inicial()
            datos_jugador = estado.jugadores_conectados[id_jugador]
            datos_jugador["x"] = x_inicial
            datos_jugador["y"] = y_inicial
            datos_jugador["dir_x"] = 0
            datos_jugador["dir_y"] = 0

    estado.bandera_al_centro()


def hay_jugadores_suficientes():
    return estado.cantidad_jugadores() >= MIN_JUGADORES


def cancelar_countdown():
    estado.countdown_actual = None
    estado.fase_partida = "lobby"
    estado.enviar_lobby_a_todos()
    registro.log_evento("Countdown cancelado: quedan menos de", MIN_JUGADORES, "jugadores")


def iniciar_countdown():
    if estado.fase_partida != "lobby":
        return

    if not hay_jugadores_suficientes():
        registro.log_evento("Se necesitan al menos", MIN_JUGADORES, "jugadores para iniciar")
        return

    estado.fase_partida = "countdown"
    segundos_restantes = COUNTDOWN_SEGUNDOS

    while segundos_restantes > 0:
        if not hay_jugadores_suficientes():
            cancelar_countdown()
            return

        estado.countdown_actual = segundos_restantes
        estado.enviar_a_todos({"type": "countdown", "seconds": segundos_restantes})
        registro.log_evento("Countdown:", segundos_restantes)

        time.sleep(1)
        segundos_restantes = segundos_restantes - 1

    estado.countdown_actual = None
    colocar_jugadores_en_spawn()

    estado.enviar_a_todos({"type": "start"})
    estado.fase_partida = "playing"
    registro.log_evento("La partida ha iniciado")


def terminar_partida(id_del_ganador):
    estado.juego_terminado = True
    estado.fase_partida = "finished"
    estado.id_ganador = id_del_ganador
    estado.nombre_ganador = estado.jugadores_conectados[id_del_ganador]["nombre"]

    mensaje_ganador = {
        "type": "game_over",
        "winner": id_del_ganador,
        "winner_name": estado.nombre_ganador,
    }
    estado.enviar_a_todos(mensaje_ganador)
    registro.log_evento(estado.nombre_ganador, "gano la partida")

    hilo = threading.Thread(target=volver_al_lobby)
    hilo.daemon = True
    hilo.start()


def volver_al_lobby():
    time.sleep(POST_GAME_SEGUNDOS)

    estado.juego_terminado = False
    estado.id_ganador = None
    estado.nombre_ganador = None
    estado.bandera_al_centro()

    estado.fase_partida = "lobby"
    estado.enviar_lobby_a_todos()
    registro.log_evento("De vuelta en el lobby")


def mover_a_todos(segundos_entre_ticks):
    for id_jugador in estado.ids_conectados():
        if id_jugador in estado.jugadores_conectados:
            datos_jugador = estado.jugadores_conectados[id_jugador]
            fisica.mover_jugador(datos_jugador, segundos_entre_ticks)


def actualizar_bandera_y_victoria():
    portador = estado.bandera["owner"]

    if portador is None:
        return False

    if portador not in estado.jugadores_conectados:
        return False

    jugador_portador = estado.jugadores_conectados[portador]
    estado.bandera["x"] = jugador_portador["x"]
    estado.bandera["y"] = jugador_portador["y"]

    dentro = fisica.esta_dentro_del_circulo(estado.bandera["x"], estado.bandera["y"])

    if dentro:
        estado.bandera["puede_ganar"] = True
        return False

    if estado.bandera["puede_ganar"]:
        terminar_partida(portador)
        return True

    return False


def enviar_state_a_todos():
    lista_jugadores = []

    for id_jugador in estado.ids_conectados():
        if id_jugador in estado.jugadores_conectados:
            datos_jugador = estado.jugadores_conectados[id_jugador]
            lista_jugadores.append({
                "id": id_jugador,
                "x": round(datos_jugador["x"], 1),
                "y": round(datos_jugador["y"], 1),
            })

    mensaje_state = {
        "type": "state",
        "flag": {
            "owner": estado.bandera["owner"],
            "x": round(estado.bandera["x"], 1),
            "y": round(estado.bandera["y"], 1),
        },
        "players": lista_jugadores,
    }

    estado.enviar_a_todos(mensaje_state)


def ciclo_de_estado():
    segundos_entre_ticks = 1 / CONFIG_DEFAULT["tick_rate"]

    while True:
        time.sleep(segundos_entre_ticks)

        if estado.fase_partida != "playing":
            continue

        mover_a_todos(segundos_entre_ticks)

        hubo_ganador = actualizar_bandera_y_victoria()

        if hubo_ganador:
            continue

        enviar_state_a_todos()