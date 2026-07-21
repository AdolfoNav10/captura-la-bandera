import pygame
import threading
from src.servidor import redServidor
from src.comun.constantes import CONFIG_DEFAULT

ANCHO_VENTANA = 900
ALTO_VENTANA = 900


def escalar_posicion(x, y):
    escala = ANCHO_VENTANA / CONFIG_DEFAULT["map_size"]
    return x * escala, y * escala


def ventana_servidor():
    pygame.init()
    ventana = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
    pygame.display.set_caption("Servidor - Captura la Bandera")
    fuente = pygame.font.SysFont(None, 32)

    color_fondo = (30, 33, 38)
    color_jugador = (80, 130, 220)
    color_bandera = (232, 147, 12)
    color_circulo = (90, 95, 105)
    color_texto = (235, 238, 242)

    ejecutando = True
    while ejecutando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN:
                    if redServidor.fase_partida == "lobby":
                        hilo_countdown = threading.Thread(target=redServidor.iniciar_countdown)
                        hilo_countdown.start()

        ventana.fill(color_fondo)

        x_centro, y_centro = escalar_posicion(CONFIG_DEFAULT["map_size"] / 2, CONFIG_DEFAULT["map_size"] / 2)
        radio_pantalla = CONFIG_DEFAULT["circle_radius"] * (ANCHO_VENTANA / CONFIG_DEFAULT["map_size"])
        pygame.draw.circle(ventana, color_circulo, (int(x_centro), int(y_centro)), int(radio_pantalla), 2)

        x_bandera, y_bandera = escalar_posicion(redServidor.bandera["x"], redServidor.bandera["y"])
        pygame.draw.circle(ventana, color_bandera, (int(x_bandera), int(y_bandera)), 10)

        for id_jugador in list(redServidor.jugadores_conectados.keys()):
            if id_jugador in redServidor.jugadores_conectados:
                datos_jugador = redServidor.jugadores_conectados[id_jugador]
                x_pantalla, y_pantalla = escalar_posicion(datos_jugador["x"], datos_jugador["y"])
                pygame.draw.circle(ventana, color_jugador, (int(x_pantalla), int(y_pantalla)), 8)

        if redServidor.fase_partida == "lobby":
            cantidad = len(redServidor.jugadores_conectados)
            texto = fuente.render("Lobby - presiona ENTER para iniciar (" + str(cantidad) + " jugadores)", True, color_texto)
            ventana.blit(texto, (20, 20))

        pygame.display.flip()

    pygame.quit()


def iniciar():
    redServidor.iniciar_servidor_en_hilos()
    ventana_servidor()


if __name__ == "__main__":
    iniciar()