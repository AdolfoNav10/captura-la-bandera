import pygame
import socket
import threading
from src.comun import protocolo as p

PUERTO_JUEGO = 8889
ANCHO_VENTANA = 900
ALTO_VENTANA = 900

ultimo_state = {"players": [], "flag": {"owner": None, "x": 500, "y": 500}}
config_juego = {"map_size": 1000}


def escuchar_servidor(ip_servidor):
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((ip_servidor, PUERTO_JUEGO))

    mensaje_join = {
        "type": "join",
        "name": "Gaby",
    }
    p.enviar(cliente, mensaje_join)

    lector = p.LectorMensajes()

    while True:
        datos_recibidos = cliente.recv(1024)
        mensajes = lector.agregar_bytes(datos_recibidos)
        for mensaje in mensajes:
            if mensaje["type"] == "welcome":
                config_juego["map_size"] = mensaje["config"]["map_size"]
            if mensaje["type"] == "state":
                ultimo_state["players"] = mensaje["players"]
                ultimo_state["flag"] = mensaje["flag"]


def escalar_posicion(x, y):
    escala = ANCHO_VENTANA / config_juego["map_size"]
    x_pantalla = x * escala
    y_pantalla = y * escala
    return x_pantalla, y_pantalla


def iniciar_ventana(ip_servidor):
    hilo_red = threading.Thread(target=escuchar_servidor, args=(ip_servidor,))
    hilo_red.daemon = True
    hilo_red.start()

    pygame.init()
    ventana = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
    pygame.display.set_caption("Captura la Bandera")

    color_fondo = (235, 238, 242)
    color_jugador = (80, 130, 220)
    color_bandera = (232, 147, 12)

    ejecutando = True
    while ejecutando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False

        ventana.fill(color_fondo)

        x_bandera, y_bandera = escalar_posicion(ultimo_state["flag"]["x"], ultimo_state["flag"]["y"])
        pygame.draw.circle(ventana, color_bandera, (int(x_bandera), int(y_bandera)), 10)

        for jugador in ultimo_state["players"]:
            x_pantalla, y_pantalla = escalar_posicion(jugador["x"], jugador["y"])
            pygame.draw.circle(ventana, color_jugador, (int(x_pantalla), int(y_pantalla)), 8)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    iniciar_ventana("localhost")