

import pygame

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


def dibujar_resplandor(ventana, color, x, y, radio):
    lado = radio * 6
    superficie = pygame.Surface((lado, lado), pygame.SRCALPHA)
    centro = lado // 2

    pygame.draw.circle(superficie, (color[0], color[1], color[2], 30), (centro, centro), radio * 2)
    pygame.draw.circle(superficie, (color[0], color[1], color[2], 70), (centro, centro), int(radio * 1.4))

    ventana.blit(superficie, (x - centro, y - centro))


def dibujar_texto(ventana, fuente, texto, x, y, color):
    imagen = fuente.render(texto, True, color)
    ventana.blit(imagen, (x, y))
    return imagen.get_width()


def dibujar_texto_centrado(ventana, fuente, texto, centro_x, y, color):
    imagen = fuente.render(texto, True, color)
    ventana.blit(imagen, (centro_x - imagen.get_width() / 2, y))


def dibujar_arena(ventana, offset_x, offset_y, lado, map_size, circle_radius):
    escala = lado / map_size

    for paso in range(1, 10):
        posicion = int(paso * lado / 10)
        pygame.draw.line(ventana, COLOR_REJILLA, (offset_x + posicion, offset_y), (offset_x + posicion, offset_y + lado), 1)
        pygame.draw.line(ventana, COLOR_REJILLA, (offset_x, offset_y + posicion), (offset_x + lado, offset_y + posicion), 1)

    pygame.draw.rect(ventana, COLOR_BORDE_PANEL, (offset_x, offset_y, lado, lado), 2)

    centro_x = offset_x + lado / 2
    centro_y = offset_y + lado / 2
    radio_pantalla = int(circle_radius * escala)

    superficie = pygame.Surface((lado, lado), pygame.SRCALPHA)
    pygame.draw.circle(superficie, (0, 200, 255, 18), (lado // 2, lado // 2), radio_pantalla)
    pygame.draw.circle(superficie, (0, 200, 255, 60), (lado // 2, lado // 2), radio_pantalla, 6)
    ventana.blit(superficie, (offset_x, offset_y))

    pygame.draw.circle(ventana, COLOR_ARENA, (int(centro_x), int(centro_y)), radio_pantalla, 2)


def dibujar_bandera(ventana, x, y, tamano):
    dibujar_resplandor(ventana, COLOR_BANDERA, x, y, tamano)

    alto_asta = tamano * 4
    base_y = y + tamano
    punta_y = base_y - alto_asta
    grosor = max(2, tamano // 3)

    pygame.draw.line(ventana, COLOR_TEXTO, (x, base_y), (x, punta_y), grosor)

    puntos = [
        (x, punta_y),
        (x + tamano * 3, punta_y + tamano),
        (x, punta_y + tamano * 2),
    ]
    pygame.draw.polygon(ventana, COLOR_BANDERA, puntos)

    pygame.draw.circle(ventana, COLOR_BANDERA, (x, base_y), max(3, tamano))


def dibujar_jugador(ventana, fuente, x, y, radio, color, numero, es_portador, es_mio):
    dibujar_resplandor(ventana, color, x, y, radio)
    pygame.draw.circle(ventana, color, (x, y), radio)

    if es_portador:
        pygame.draw.circle(ventana, COLOR_BANDERA, (x, y), radio + 6, 2)

    if es_mio:
        pygame.draw.circle(ventana, COLOR_TEXTO, (x, y), radio + 11, 1)

    etiqueta = fuente.render(str(numero), True, (8, 8, 14))
    ventana.blit(etiqueta, (x - etiqueta.get_width() / 2, y - etiqueta.get_height() / 2))


def dibujar_panel_jugadores(ventana, fuentes, x_panel, ancho_panel, alto_ventana, filas, titulo, pie):
    pygame.draw.rect(ventana, COLOR_PANEL, (x_panel, 0, ancho_panel, alto_ventana))
    pygame.draw.line(ventana, COLOR_BORDE_PANEL, (x_panel, 0), (x_panel, alto_ventana), 2)

    margen = 22
    dibujar_texto(ventana, fuentes["titulo_panel"], titulo, x_panel + margen, 26, COLOR_ACENTO)
    pygame.draw.line(ventana, COLOR_BORDE_PANEL, (x_panel + margen, 62), (x_panel + ancho_panel - margen, 62), 1)

    y_fila = 82
    alto_fila = 42
    espacio_disponible = alto_ventana - 150
    maximo_filas = int(espacio_disponible / alto_fila)
    mostradas = 0

    for fila in filas:
        if mostradas >= maximo_filas:
            restantes = len(filas) - mostradas
            dibujar_texto(ventana, fuentes["panel"], "+ " + str(restantes) + " mas", x_panel + margen, y_fila, COLOR_APAGADO)
            break

        centro_punto = (x_panel + margen + 14, y_fila + 12)
        pygame.draw.circle(ventana, fila["color"], centro_punto, 13)

        etiqueta = fuentes["numero_panel"].render(str(fila["numero"]), True, (8, 8, 14))
        ventana.blit(etiqueta, (centro_punto[0] - etiqueta.get_width() / 2, centro_punto[1] - etiqueta.get_height() / 2))

        color_nombre = COLOR_TEXTO
        if fila["es_mio"]:
            color_nombre = fila["color"]

        nombre = fila["nombre"]
        if len(nombre) > 14:
            nombre = nombre[:14] + "."

        ancho_nombre = dibujar_texto(ventana, fuentes["panel"], nombre, x_panel + margen + 38, y_fila, color_nombre)

        if fila["es_portador"]:
            dibujar_texto(ventana, fuentes["panel"], "*", x_panel + margen + 46 + ancho_nombre, y_fila, COLOR_BANDERA)

        y_fila = y_fila + alto_fila
        mostradas = mostradas + 1

    y_pie = alto_ventana - 58
    pygame.draw.line(ventana, COLOR_BORDE_PANEL, (x_panel + margen, y_pie - 14), (x_panel + ancho_panel - margen, y_pie - 14), 1)

    for linea in pie:
        dibujar_texto(ventana, fuentes["pie"], linea, x_panel + margen, y_pie, COLOR_APAGADO)
        y_pie = y_pie + 22