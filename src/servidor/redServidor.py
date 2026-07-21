import socket
import threading
import time
import random
import math
from src.comun import protocolo as p
from src.comun.constantes import CONFIG_DEFAULT
import json

PUERTO_JUEGO = 8889

jugadores_conectados = {}
bandera = {"owner": None, "x": 500, "y": 500}
juego_terminado = False


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

    for id_jugador in jugadores_conectados:
        conexion_jugador = jugadores_conectados[id_jugador]["conexion"]
        p.enviar(conexion_jugador, mensaje_lobby)


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
    global juego_terminado
    tick_rate = CONFIG_DEFAULT["tick_rate"]
    segundos_entre_ticks = 1 / tick_rate

    while True:
        time.sleep(segundos_entre_ticks)

        if not juego_terminado:
            for id_jugador in jugadores_conectados:
                datos_jugador = jugadores_conectados[id_jugador]
                mover_jugador(datos_jugador, segundos_entre_ticks)

            if bandera["owner"] is not None:
                jugador_portador = jugadores_conectados[bandera["owner"]]
                bandera["x"] = jugador_portador["x"]
                bandera["y"] = jugador_portador["y"]

            if bandera["owner"] is not None:
                centro = CONFIG_DEFAULT["map_size"] / 2
                radio_limite = CONFIG_DEFAULT["circle_radius"] + CONFIG_DEFAULT["player_radius"]
                distancia_al_centro = calcular_distancia(bandera["x"], bandera["y"], centro, centro)

                if distancia_al_centro > radio_limite:
                    juego_terminado = True
                    mensaje_ganador = {
                        "type": "game_over",
                        "winner": bandera["owner"],
                    }
                    for id_jugador in jugadores_conectados:
                        conexion_jugador = jugadores_conectados[id_jugador]["conexion"]
                        p.enviar(conexion_jugador, mensaje_ganador)
                    print(bandera["owner"], "gano la partida")

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
                    "dir_x": 0,
                    "dir_y": 0,
                }
                print("Jugadores conectados ahora:", jugadores_conectados)

                respuesta = {
                    "type": "welcome",
                    "player_id": id_jugador,
                    "config": CONFIG_DEFAULT,
                }
                p.enviar(conexion, respuesta)

                enviar_lobby_a_todos()

            if mensaje["type"] == "input":
                jugadores_conectados[id_jugador]["dir_x"] = mensaje["dir"]["x"]
                jugadores_conectados[id_jugador]["dir_y"] = mensaje["dir"]["y"]

            if mensaje["type"] == "interact":
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






def escuchar_descubrimiento():
    socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socket_udp.bind(("0.0.0.0", 8888))
    print("Escuchando descubrimiento en el puerto UDP 8888")

    lector = p.LectorMensajes()

    while True:
        datos, direccion_cliente = socket_udp.recvfrom(1024)
        mensajes = lector.agregar_bytes(datos)

        for mensaje in mensajes:
            if mensaje["type"] == "discover":
                respuesta = {
                    "type": "server_info",
                    "name": "Servidor de Gaby",
                    "tcp_port": PUERTO_JUEGO,
                    "state": "lobby",
                    "players": len(jugadores_conectados),
                }
                texto_respuesta = json.dumps(respuesta) + "\n"
                socket_udp.sendto(texto_respuesta.encode("utf-8"), direccion_cliente)
                print("Respondi a un discover desde", direccion_cliente)



def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(("0.0.0.0", PUERTO_JUEGO))
    servidor.listen()
    print("Servidor esperando conexiones en el puerto", PUERTO_JUEGO)

    hilo_estado = threading.Thread(target=ciclo_de_estado)
    hilo_estado.start()

    hilo_descubrimiento = threading.Thread(target=escuchar_descubrimiento)
    hilo_descubrimiento.start()

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