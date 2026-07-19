import socket
import threading
from src.comun import protocolo as p
from src.comun.constantes import CONFIG_DEFAULT

PUERTO_JUEGO = 8889

jugadores_conectados = {}


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


def atender_cliente(conexion, direccion, id_jugador):
    lector = p.LectorMensajes()
    datos_recibidos = conexion.recv(1024)
    mensajes = lector.agregar_bytes(datos_recibidos)

    for mensaje in mensajes:
        print("Mensaje recibido de", id_jugador, ":", mensaje)
        if mensaje["type"] == "join":
            jugadores_conectados[id_jugador] = {
                "nombre": mensaje["name"],
                "conexion": conexion,
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