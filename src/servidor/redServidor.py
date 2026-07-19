import socket
import threading
import time
import random
import math
from src.comun import protocolo as p
from src.comun.constantes import CONFIG_DEFAULT

PUERTO_JUEGO = 8889

jugadores_conectados = {}


def generar_posicion_inicial():
    centro = CONFIG_DEFAULT["map_size"] / 2
    radio_circulo = CONFIG_DEFAULT["circle_radius"]

    while True:
        x = random.uniform(0, CONFIG_DEFAULT["map_size"])
        y = random.uniform(0, CONFIG_DEFAULT["map_size"])
        distancia_al_centro = math.sqrt((x - centro) ** 2 + (y - centro) ** 2)
        if distancia_al_centro > radio_circulo:
            return x, y


def enviar_lobby_a_todos():
    lista_jugadores = []
    for id_jugador in jugadores_conectados:
        nombre = jugadores_conectados[id_jugador]["nombre"]
        lista_jugadores.append({"id": id_jugador, "name": nombre})

    mensaje_lobby = {
        "type": "lobby",
        "players": lista_jugadores,
    }

    for id_jugador in jugadores_conectados:
        conexion_jugador = jugadores_conectados[id_jugador]["conexion"]
        p.enviar(conexion_jugador, mensaje_lobby)


def ciclo_de_estado():
    tick_rate = CONFIG_DEFAULT["tick_rate"]
    segundos_entre_ticks = 1 / tick_rate

    while True:
        time.sleep(segundos_entre_ticks)

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
            "flag": {"owner": None, "x": 500, "y": 500},
            "players": lista_jugadores,
        }

        for id_jugador in jugadores_conectados:
            conexion_jugador = jugadores_conectados[id_jugador]["conexion"]
            p.enviar(conexion_jugador, mensaje_state)


def atender_cliente(conexion, direccion, id_jugador):
    lector = p.LectorMensajes()

    while True:
        datos_recibidos = conexion.recv(1024)
        mensajes = lector.agregar_bytes(datos_recibidos)

        for mensaje in mensajes:
            print("Mensaje recibido de", id_jugador, ":", mensaje)
            if mensaje["type"] == "join":
                x_inicial, y_inicial = generar_posicion_inicial()
                jugadores_conectados[id_jugador] = {
                    "nombre": mensaje["name"],
                    "conexion": conexion,
                    "x": x_inicial,
                    "y": y_inicial,
                }
                print("Jugadores conectados ahora:", jugadores_conectados)

                respuesta = {
                    "type": "welcome",
                    "player_id": id_jugador,
                    "config": CONFIG_DEFAULT,
                }
                p.enviar(conexion, respuesta)

                enviar_lobby_a_todos()


def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(("0.0.0.0", PUERTO_JUEGO))
    servidor.listen()
    print("Servidor esperando conexiones en el puerto", PUERTO_JUEGO)

    hilo_estado = threading.Thread(target=ciclo_de_estado)
    hilo_estado.start()

    contador_jugadores = 0

    while True:
        conexion, direccion = servidor.accept()
        contador_jugadores = contador_jugadores + 1
        id_jugador = "p" + str(contador_jugadores)
        print("Se conecto un cliente desde", direccion, "- asignado como", id_jugador)

        hilo = threading.Thread(target=atender_cliente, args=(conexion, direccion, id_jugador))
        hilo.start()


if __name__ == "__main__":
    iniciar_servidor()