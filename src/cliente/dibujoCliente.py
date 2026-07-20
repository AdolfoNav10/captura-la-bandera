import pygame
import socket
import threading
from src.comun import protocolo as p

PUERTO_JUEGO = 8889
ANCHO_VENTANA = 900
ALTO_VENTANA = 900

ultimo_state = {"players": [], "flag": {"owner": None, "x": 500, "y": 500}}
config_juego = {"map_size": 1000}
conexion_servidor = None


def escuchar_servidor(ip_servidor):
    global conexion_servidor

    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((ip_servidor, PUERTO_JUEGO))
    conexion_servidor = cliente

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


def calcular_direccion_actual():
    teclas_presionadas = pygame.key.get_pressed()

    direccion_x = 0
    direccion_y = 0

    if teclas_presionadas[pygame.K_a]:
        direccion_x = -1
    if teclas_presionadas[pygame.K_d]:
        direccion_x = 1
    if teclas_presionadas[pygame.K_w]:
        direccion_y = -1
    if teclas_presionadas[pygame.K_s]:
        direccion_y = 1

    return direccion_x, direccion_y


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

    ultima_direccion_enviada = (0, 0)

    ejecutando = True
    while ejecutando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False

        direccion_actual = calcular_direccion_actual()

        if direccion_actual != ultima_direccion_enviada and conexion_servidor is not None:
            mensaje_input = {
                "type": "input",
                "dir": {"x": direccion_actual[0], "y": direccion_actual[1]},
            }
            p.enviar(conexion_servidor, mensaje_input)
            ultima_direccion_enviada = direccion_actual

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