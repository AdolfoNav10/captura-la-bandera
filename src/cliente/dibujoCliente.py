import pygame
import socket
import threading
import json
import random
from src.comun import protocolo as p

ANCHO_VENTANA = 950
ALTO_VENTANA = 950

ultimo_state = {"players": [], "flag": {"owner": None, "x": 500, "y": 500}}
config_juego = {"map_size": 1000, "circle_radius": 300}
info_partida = {"mi_id": None, "ganador": None}
conexion_servidor = None


def descubrir_servidor():
    socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    socket_udp.settimeout(2)

    mensaje_discover = {"type": "discover", "v": 1}
    texto_discover = json.dumps(mensaje_discover) + "\n"
    socket_udp.sendto(texto_discover.encode("utf-8"), ("255.255.255.255", 8888))

    lector = p.LectorMensajes()

    try:
        datos, direccion_servidor = socket_udp.recvfrom(1024)

        if not datos.endswith(b"\n"):
            datos = datos + b"\n"

        mensajes = lector.agregar_bytes(datos)
        for mensaje in mensajes:
            if mensaje.get("type") == "server_info":
                ip_encontrada = direccion_servidor[0]
                puerto_encontrado = mensaje["tcp_port"]
                print("Servidor encontrado:", mensaje.get("name"), "en", ip_encontrada)
                return ip_encontrada, puerto_encontrado
    except socket.timeout:
        print("No se encontro ningun servidor por broadcast")

    return None, None


def escuchar_servidor():
    global conexion_servidor

    ip_servidor, puerto_servidor = descubrir_servidor()

    if ip_servidor is None:
        respuesta = input("No se encontro servidor. Escribe la IP del servidor (o Enter para salir): ").strip()
        if respuesta == "":
            print("No se pudo conectar")
            return
        ip_servidor = respuesta
        puerto_servidor = 8889

    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((ip_servidor, puerto_servidor))
    conexion_servidor = cliente

    nombre_jugador = "Jugador" + str(random.randint(100, 999))

    mensaje_join = {
        "type": "join",
        "v": 1,
        "name": nombre_jugador,
    }
    p.enviar(cliente, mensaje_join)

    lector = p.LectorMensajes()

    while True:
        datos_recibidos = cliente.recv(1024)
        mensajes = lector.agregar_bytes(datos_recibidos)
        for mensaje in mensajes:
            if mensaje.get("type") == "welcome":
                config_juego["map_size"] = mensaje["config"]["map_size"]
                config_juego["circle_radius"] = mensaje["config"]["circle_radius"]
                info_partida["mi_id"] = mensaje["player_id"]
            if mensaje.get("type") == "state":
                ultimo_state["players"] = mensaje["players"]
                ultimo_state["flag"] = mensaje["flag"]
            if mensaje.get("type") == "countdown":
                print("Countdown:", mensaje["seconds"])
            if mensaje.get("type") == "start":
                print("La partida ha comenzado")
            if mensaje.get("type") == "game_over":
                info_partida["ganador"] = mensaje["winner"]
            if mensaje.get("type") == "error":
                print("Error del servidor:", mensaje["reason"])


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


def iniciar_ventana():
    hilo_red = threading.Thread(target=escuchar_servidor)
    hilo_red.daemon = True
    hilo_red.start()

    pygame.init()
    ventana = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
    pygame.display.set_caption("Captura la Bandera")
    fuente = pygame.font.SysFont(None, 52)

    color_fondo = (16, 16, 20)
    color_jugador = (165, 0, 68)
    color_bandera = (237, 187, 0)
    color_circulo = (0, 77, 152)

    ultima_direccion_enviada = (0, 0)

    ejecutando = True
    while ejecutando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    if conexion_servidor is not None:
                        mensaje_interact = {"type": "interact"}
                        p.enviar(conexion_servidor, mensaje_interact)

        direccion_actual = calcular_direccion_actual()

        if direccion_actual != ultima_direccion_enviada and conexion_servidor is not None:
            mensaje_input = {
                "type": "input",
                "dir": {"x": direccion_actual[0], "y": direccion_actual[1]},
            }
            p.enviar(conexion_servidor, mensaje_input)
            ultima_direccion_enviada = direccion_actual

        ventana.fill(color_fondo)

        x_centro, y_centro = escalar_posicion(config_juego["map_size"] / 2, config_juego["map_size"] / 2)
        radio_pantalla = config_juego["circle_radius"] * (ANCHO_VENTANA / config_juego["map_size"])
        pygame.draw.circle(ventana, color_circulo, (int(x_centro), int(y_centro)), int(radio_pantalla), 2)

        x_bandera, y_bandera = escalar_posicion(ultimo_state["flag"]["x"], ultimo_state["flag"]["y"])
        pygame.draw.circle(ventana, color_bandera, (int(x_bandera), int(y_bandera)), 10)

        for jugador in ultimo_state["players"]:
            x_pantalla, y_pantalla = escalar_posicion(jugador["x"], jugador["y"])
            pygame.draw.circle(ventana, color_jugador, (int(x_pantalla), int(y_pantalla)), 8)

        if info_partida["ganador"] is not None:
            if info_partida["ganador"] == info_partida["mi_id"]:
                texto = fuente.render("Has ganado!", True, color_bandera)
            else:
                texto = fuente.render("Gano " + info_partida["ganador"], True, (240, 240, 245))
            ventana.blit(texto, (ANCHO_VENTANA / 2 - texto.get_width() / 2, 40))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    iniciar_ventana()