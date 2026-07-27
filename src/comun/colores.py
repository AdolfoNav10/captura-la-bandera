# src/comun/colores.py

COLOR_FONDO = (8, 8, 14)
COLOR_REJILLA = (24, 26, 42)
COLOR_PANEL = (13, 14, 24)
COLOR_BORDE_PANEL = (38, 42, 68)
COLOR_ARENA = (0, 200, 255)
COLOR_BANDERA = (255, 214, 0)
COLOR_TEXTO = (235, 240, 255)
COLOR_APAGADO = (118, 128, 158)
COLOR_ERROR = (255, 60, 120)
COLOR_ACENTO = (255, 45, 149)

PALETA_JUGADORES = [
    (0, 240, 255),
    (255, 45, 149),
    (57, 255, 20),
    (255, 145, 0),
    (170, 110, 255),
    (255, 240, 60),
    (0, 255, 170),
    (255, 90, 90),
]


def color_de_jugador(numero):
    return PALETA_JUGADORES[numero % len(PALETA_JUGADORES)]


def numero_visible(id_jugador, posicion_en_lista):
    digitos = ""

    for caracter in str(id_jugador):
        if caracter.isdigit():
            digitos = digitos + caracter

    if digitos != "":
        return int(digitos)

    return posicion_en_lista + 1