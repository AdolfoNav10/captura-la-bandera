import pygame
import threading
from src.servidor import redServidor
from src.comun import estilo as es
from src.comun.constantes import CONFIG_DEFAULT, MIN_JUGADORES

ANCHO_PANEL = 320

ancho_ventana = 0
alto_ventana = 0
lado_juego = 0
offset_x = 0
offset_y = 0
x_panel = 0


def escalar_posicion(x, y):
    escala = lado_juego / CONFIG_DEFAULT["map_size"]
    return offset_x + x * escala, offset_y + y * escala


def filas_del_panel():
    portador = redServidor.bandera["owner"]
    filas = []
    posicion = 0

    for id_jugador in list(redServidor.jugadores_conectados.keys()):
        if id_jugador in redServidor.jugadores_conectados:
            numero = es.numero_visible(id_jugador, posicion)
            filas.append({
                "numero": numero,
                "nombre": redServidor.jugadores_conectados[id_jugador]["nombre"],
                "color": es.color_de_jugador(numero),
                "es_portador": id_jugador == portador,
                "es_mio": False,
            })
            posicion = posicion + 1

    return filas


def ventana_servidor():
    global ancho_ventana, alto_ventana, lado_juego, offset_x, offset_y, x_panel

    pygame.init()
    info_pantalla = pygame.display.Info()
    ancho_ventana = info_pantalla.current_w - 60
    alto_ventana = info_pantalla.current_h - 100

    zona_juego = ancho_ventana - ANCHO_PANEL
    lado_juego = min(zona_juego, alto_ventana) - 60
    offset_x = (zona_juego - lado_juego) // 2
    offset_y = (alto_ventana - lado_juego) // 2
    x_panel = ancho_ventana - ANCHO_PANEL

    ventana = pygame.display.set_mode((ancho_ventana, alto_ventana))
    pygame.display.set_caption("Servidor - Captura la Bandera")
    reloj = pygame.time.Clock()

    fuentes = {
        "normal": pygame.font.SysFont(None, 38),
        "grande": pygame.font.SysFont(None, 62),
        "countdown": pygame.font.SysFont(None, 190),
        "titulo_panel": pygame.font.SysFont(None, 34),
        "panel": pygame.font.SysFont(None, 30),
        "numero_panel": pygame.font.SysFont(None, 22),
        "numero": pygame.font.SysFont(None, 24),
        "pie": pygame.font.SysFont(None, 24),
    }

    radio_jugador = max(6, int(CONFIG_DEFAULT["player_radius"] * lado_juego / CONFIG_DEFAULT["map_size"]))
    centro_x_juego = zona_juego / 2

    ejecutando = True
    while ejecutando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN:
                    if redServidor.fase_partida == "lobby":
                        hilo_countdown = threading.Thread(target=redServidor.iniciar_countdown)
                        hilo_countdown.daemon = True
                        hilo_countdown.start()

        ventana.fill(es.COLOR_FONDO)
        es.dibujar_arena(ventana, offset_x, offset_y, lado_juego, CONFIG_DEFAULT["map_size"], CONFIG_DEFAULT["circle_radius"])

        fase = redServidor.fase_partida
        portador = redServidor.bandera["owner"]

        if fase == "playing" or fase == "finished":
            x_bandera, y_bandera = escalar_posicion(redServidor.bandera["x"], redServidor.bandera["y"])
            es.dibujar_bandera(ventana, int(x_bandera), int(y_bandera), max(4, radio_jugador // 2))

            posicion = 0
            for id_jugador in list(redServidor.jugadores_conectados.keys()):
                if id_jugador in redServidor.jugadores_conectados:
                    datos_jugador = redServidor.jugadores_conectados[id_jugador]
                    numero = es.numero_visible(id_jugador, posicion)
                    x_pantalla, y_pantalla = escalar_posicion(datos_jugador["x"], datos_jugador["y"])
                    es.dibujar_jugador(
                        ventana, fuentes["numero"],
                        int(x_pantalla), int(y_pantalla), radio_jugador,
                        es.color_de_jugador(numero), numero,
                        id_jugador == portador, False,
                    )
                    posicion = posicion + 1

        cantidad = len(redServidor.jugadores_conectados)

        if fase == "lobby":
            if cantidad >= MIN_JUGADORES:
                es.dibujar_texto_centrado(ventana, fuentes["grande"], "ENTER para iniciar", centro_x_juego, alto_ventana * 0.44, es.COLOR_ARENA)
            else:
                es.dibujar_texto_centrado(ventana, fuentes["grande"], "Faltan jugadores (" + str(cantidad) + " de " + str(MIN_JUGADORES) + ")", centro_x_juego, alto_ventana * 0.44, es.COLOR_APAGADO)

        if fase == "countdown" and redServidor.countdown_actual is not None:
            es.dibujar_texto_centrado(ventana, fuentes["normal"], "La partida comienza en", centro_x_juego, alto_ventana * 0.30, es.COLOR_TEXTO)
            es.dibujar_texto_centrado(ventana, fuentes["countdown"], str(redServidor.countdown_actual), centro_x_juego, alto_ventana * 0.36, es.COLOR_BANDERA)

        if fase == "finished" and redServidor.nombre_ganador is not None:
            es.dibujar_texto_centrado(ventana, fuentes["grande"], "GANADOR: " + redServidor.nombre_ganador, centro_x_juego, 24, es.COLOR_BANDERA)

        titulo_panel = "JUGADORES  (" + str(cantidad) + ")"
        pie = ["Fase: " + fase, "ENTER inicia la partida"]
        es.dibujar_panel_jugadores(ventana, fuentes, x_panel, ANCHO_PANEL, alto_ventana, filas_del_panel(), titulo_panel, pie)

        pygame.display.flip()
        reloj.tick(60)

    pygame.quit()


def iniciar():
    redServidor.iniciar_servidor_en_hilos()
    ventana_servidor()


if __name__ == "__main__":
    iniciar()