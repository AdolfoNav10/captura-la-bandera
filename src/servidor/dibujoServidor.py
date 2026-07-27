# src/servidor/dibujoServidor.py

import pygame
import threading

from src.comun import estilo as es
from src.comun.constantes import CONFIG_DEFAULT, MIN_JUGADORES
from src.servidor import redServidor
from src.servidor import estado_partida as estado
from src.servidor import ciclo_partida

ANCHO_PANEL = 320

geometria = {
    "ancho": 0,
    "alto": 0,
    "lado": 0,
    "offset_x": 0,
    "offset_y": 0,
    "x_panel": 0,
    "centro_juego": 0,
    "radio_jugador": 8,
}


def calcular_geometria():
    info_pantalla = pygame.display.Info()
    ancho = info_pantalla.current_w - 60
    alto = info_pantalla.current_h - 100

    zona_juego = ancho - ANCHO_PANEL
    lado = min(zona_juego, alto) - 60

    geometria["ancho"] = ancho
    geometria["alto"] = alto
    geometria["lado"] = lado
    geometria["offset_x"] = (zona_juego - lado) // 2
    geometria["offset_y"] = (alto - lado) // 2
    geometria["x_panel"] = ancho - ANCHO_PANEL
    geometria["centro_juego"] = zona_juego / 2
    geometria["radio_jugador"] = max(6, int(CONFIG_DEFAULT["player_radius"] * lado / CONFIG_DEFAULT["map_size"]))


def crear_fuentes():
    return {
        "normal": pygame.font.SysFont(None, 38),
        "grande": pygame.font.SysFont(None, 62),
        "countdown": pygame.font.SysFont(None, 190),
        "titulo_panel": pygame.font.SysFont(None, 34),
        "panel": pygame.font.SysFont(None, 30),
        "numero_panel": pygame.font.SysFont(None, 22),
        "numero": pygame.font.SysFont(None, 24),
        "pie": pygame.font.SysFont(None, 24),
    }


def escalar_posicion(x, y):
    escala = geometria["lado"] / CONFIG_DEFAULT["map_size"]
    x_pantalla = geometria["offset_x"] + x * escala
    y_pantalla = geometria["offset_y"] + y * escala
    return x_pantalla, y_pantalla


def filas_del_panel():
    portador = estado.bandera["owner"]
    filas = []
    posicion = 0

    for id_jugador in estado.ids_conectados():
        if id_jugador in estado.jugadores_conectados:
            numero = es.numero_visible(id_jugador, posicion)
            filas.append({
                "numero": numero,
                "nombre": estado.jugadores_conectados[id_jugador]["nombre"],
                "color": es.color_de_jugador(numero),
                "es_portador": id_jugador == portador,
                "es_mio": False,
            })
            posicion = posicion + 1

    return filas


def dibujar_jugadores(ventana, fuentes):
    portador = estado.bandera["owner"]
    posicion = 0

    for id_jugador in estado.ids_conectados():
        if id_jugador in estado.jugadores_conectados:
            datos_jugador = estado.jugadores_conectados[id_jugador]
            numero = es.numero_visible(id_jugador, posicion)
            x_pantalla, y_pantalla = escalar_posicion(datos_jugador["x"], datos_jugador["y"])

            es.dibujar_jugador(
                ventana, fuentes["numero"],
                int(x_pantalla), int(y_pantalla), geometria["radio_jugador"],
                es.color_de_jugador(numero), numero,
                id_jugador == portador, False,
            )
            posicion = posicion + 1


def dibujar_partida(ventana, fuentes):
    x_bandera, y_bandera = escalar_posicion(estado.bandera["x"], estado.bandera["y"])
    tamano_bandera = max(4, geometria["radio_jugador"] // 2)
    es.dibujar_bandera(ventana, int(x_bandera), int(y_bandera), tamano_bandera)

    dibujar_jugadores(ventana, fuentes)


def dibujar_aviso_lobby(ventana, fuentes):
    cantidad = estado.cantidad_jugadores()

    if cantidad >= MIN_JUGADORES:
        texto = "ENTER para iniciar"
        color = es.COLOR_ARENA
    else:
        texto = "Faltan jugadores (" + str(cantidad) + " de " + str(MIN_JUGADORES) + ")"
        color = es.COLOR_APAGADO

    es.dibujar_texto_centrado(ventana, fuentes["grande"], texto, geometria["centro_juego"], geometria["alto"] * 0.44, color)


def dibujar_countdown(ventana, fuentes):
    es.dibujar_texto_centrado(ventana, fuentes["normal"], "La partida comienza en", geometria["centro_juego"], geometria["alto"] * 0.30, es.COLOR_TEXTO)
    es.dibujar_texto_centrado(ventana, fuentes["countdown"], str(estado.countdown_actual), geometria["centro_juego"], geometria["alto"] * 0.36, es.COLOR_BANDERA)


def dibujar_ganador(ventana, fuentes):
    texto = "GANADOR: " + estado.nombre_ganador
    es.dibujar_texto_centrado(ventana, fuentes["grande"], texto, geometria["centro_juego"], 24, es.COLOR_BANDERA)


def dibujar_todo(ventana, fuentes):
    ventana.fill(es.COLOR_FONDO)

    es.dibujar_arena(
        ventana,
        geometria["offset_x"], geometria["offset_y"], geometria["lado"],
        CONFIG_DEFAULT["map_size"], CONFIG_DEFAULT["circle_radius"],
    )

    fase = estado.fase_partida

    if fase == "playing" or fase == "finished":
        dibujar_partida(ventana, fuentes)

    if fase == "lobby":
        dibujar_aviso_lobby(ventana, fuentes)

    if fase == "countdown" and estado.countdown_actual is not None:
        dibujar_countdown(ventana, fuentes)

    if fase == "finished" and estado.nombre_ganador is not None:
        dibujar_ganador(ventana, fuentes)

    titulo_panel = "JUGADORES  (" + str(estado.cantidad_jugadores()) + ")"
    pie = ["Fase: " + fase, "ENTER inicia la partida"]

    es.dibujar_panel_jugadores(
        ventana, fuentes,
        geometria["x_panel"], ANCHO_PANEL, geometria["alto"],
        filas_del_panel(), titulo_panel, pie,
    )


def manejar_tecla(evento):
    if evento.key != pygame.K_RETURN:
        return

    if estado.fase_partida != "lobby":
        return

    hilo = threading.Thread(target=ciclo_partida.iniciar_countdown)
    hilo.daemon = True
    hilo.start()


def ventana_servidor():
    pygame.init()
    calcular_geometria()

    ventana = pygame.display.set_mode((geometria["ancho"], geometria["alto"]))
    pygame.display.set_caption("Servidor - Captura la Bandera")

    reloj = pygame.time.Clock()
    fuentes = crear_fuentes()

    ejecutando = True
    while ejecutando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False

            if evento.type == pygame.KEYDOWN:
                manejar_tecla(evento)

        dibujar_todo(ventana, fuentes)
        pygame.display.flip()
        reloj.tick(60)

    pygame.quit()


def iniciar():
    redServidor.iniciar_servidor_en_hilos()
    ventana_servidor()


if __name__ == "__main__":
    iniciar()