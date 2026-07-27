# src/comun/dibujos.py

import pygame
from src.comun import colores as col


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


def dibujar_rejilla(ventana, offset_x, offset_y, lado):
    for paso in range(1, 10):
        posicion = int(paso * lado / 10)

        inicio_vertical = (offset_x + posicion, offset_y)
        final_vertical = (offset_x + posicion, offset_y + lado)
        pygame.draw.line(ventana, col.COLOR_REJILLA, inicio_vertical, final_vertical, 1)

        inicio_horizontal = (offset_x, offset_y + posicion)
        final_horizontal = (offset_x + lado, offset_y + posicion)
        pygame.draw.line(ventana, col.COLOR_REJILLA, inicio_horizontal, final_horizontal, 1)


def dibujar_circulo_central(ventana, offset_x, offset_y, lado, radio_pantalla):
    superficie = pygame.Surface((lado, lado), pygame.SRCALPHA)
    centro = lado // 2

    pygame.draw.circle(superficie, (0, 200, 255, 18), (centro, centro), radio_pantalla)
    pygame.draw.circle(superficie, (0, 200, 255, 60), (centro, centro), radio_pantalla, 6)
    ventana.blit(superficie, (offset_x, offset_y))

    centro_x = int(offset_x + lado / 2)
    centro_y = int(offset_y + lado / 2)
    pygame.draw.circle(ventana, col.COLOR_ARENA, (centro_x, centro_y), radio_pantalla, 2)


def dibujar_arena(ventana, offset_x, offset_y, lado, map_size, circle_radius):
    escala = lado / map_size
    radio_pantalla = int(circle_radius * escala)

    dibujar_rejilla(ventana, offset_x, offset_y, lado)
    pygame.draw.rect(ventana, col.COLOR_BORDE_PANEL, (offset_x, offset_y, lado, lado), 2)
    dibujar_circulo_central(ventana, offset_x, offset_y, lado, radio_pantalla)


def dibujar_bandera(ventana, x, y, tamano):
    dibujar_resplandor(ventana, col.COLOR_BANDERA, x, y, tamano)

    alto_asta = tamano * 4
    base_y = y + tamano
    punta_y = base_y - alto_asta
    grosor = max(2, tamano // 3)

    pygame.draw.line(ventana, col.COLOR_TEXTO, (x, base_y), (x, punta_y), grosor)

    puntos = [
        (x, punta_y),
        (x + tamano * 3, punta_y + tamano),
        (x, punta_y + tamano * 2),
    ]
    pygame.draw.polygon(ventana, col.COLOR_BANDERA, puntos)

    pygame.draw.circle(ventana, col.COLOR_BANDERA, (x, base_y), max(3, tamano))


def dibujar_jugador(ventana, fuente, x, y, radio, color, numero, es_portador, es_mio):
    dibujar_resplandor(ventana, color, x, y, radio)
    pygame.draw.circle(ventana, color, (x, y), radio)

    if es_portador:
        pygame.draw.circle(ventana, col.COLOR_BANDERA, (x, y), radio + 6, 2)

    if es_mio:
        pygame.draw.circle(ventana, col.COLOR_TEXTO, (x, y), radio + 11, 1)

    etiqueta = fuente.render(str(numero), True, col.COLOR_FONDO)
    ventana.blit(etiqueta, (x - etiqueta.get_width() / 2, y - etiqueta.get_height() / 2))