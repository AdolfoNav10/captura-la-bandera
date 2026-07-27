# src/comun/panel.py

import pygame
from src.comun import colores as col
from src.comun import dibujos as dib

MARGEN = 22
ALTO_FILA = 42


def dibujar_fondo_panel(ventana, x_panel, ancho_panel, alto_ventana):
    pygame.draw.rect(ventana, col.COLOR_PANEL, (x_panel, 0, ancho_panel, alto_ventana))
    pygame.draw.line(ventana, col.COLOR_BORDE_PANEL, (x_panel, 0), (x_panel, alto_ventana), 2)


def dibujar_encabezado(ventana, fuentes, x_panel, ancho_panel, titulo):
    dib.dibujar_texto(ventana, fuentes["titulo_panel"], titulo, x_panel + MARGEN, 26, col.COLOR_ACENTO)

    inicio = (x_panel + MARGEN, 62)
    final = (x_panel + ancho_panel - MARGEN, 62)
    pygame.draw.line(ventana, col.COLOR_BORDE_PANEL, inicio, final, 1)


def dibujar_fila_jugador(ventana, fuentes, x_fila, y_fila, fila):
    centro_punto = (x_fila + 14, y_fila + 12)
    pygame.draw.circle(ventana, fila["color"], centro_punto, 13)

    etiqueta = fuentes["numero_panel"].render(str(fila["numero"]), True, col.COLOR_FONDO)
    x_etiqueta = centro_punto[0] - etiqueta.get_width() / 2
    y_etiqueta = centro_punto[1] - etiqueta.get_height() / 2
    ventana.blit(etiqueta, (x_etiqueta, y_etiqueta))

    color_nombre = col.COLOR_TEXTO
    if fila["es_mio"]:
        color_nombre = fila["color"]

    nombre = fila["nombre"]
    if len(nombre) > 14:
        nombre = nombre[:14] + "."

    ancho_nombre = dib.dibujar_texto(ventana, fuentes["panel"], nombre, x_fila + 38, y_fila, color_nombre)

    if fila["es_portador"]:
        dib.dibujar_texto(ventana, fuentes["panel"], "*", x_fila + 46 + ancho_nombre, y_fila, col.COLOR_BANDERA)


def dibujar_lista_jugadores(ventana, fuentes, x_panel, alto_ventana, filas):
    x_fila = x_panel + MARGEN
    y_fila = 82
    espacio_disponible = alto_ventana - 150
    maximo_filas = int(espacio_disponible / ALTO_FILA)
    mostradas = 0

    for fila in filas:
        if mostradas >= maximo_filas:
            restantes = len(filas) - mostradas
            texto_restantes = "+ " + str(restantes) + " mas"
            dib.dibujar_texto(ventana, fuentes["panel"], texto_restantes, x_fila, y_fila, col.COLOR_APAGADO)
            return

        dibujar_fila_jugador(ventana, fuentes, x_fila, y_fila, fila)
        y_fila = y_fila + ALTO_FILA
        mostradas = mostradas + 1


def dibujar_pie_panel(ventana, fuentes, x_panel, ancho_panel, alto_ventana, lineas):
    y_pie = alto_ventana - 58

    inicio = (x_panel + MARGEN, y_pie - 14)
    final = (x_panel + ancho_panel - MARGEN, y_pie - 14)
    pygame.draw.line(ventana, col.COLOR_BORDE_PANEL, inicio, final, 1)

    for linea in lineas:
        dib.dibujar_texto(ventana, fuentes["pie"], linea, x_panel + MARGEN, y_pie, col.COLOR_APAGADO)
        y_pie = y_pie + 22


def dibujar_panel_jugadores(ventana, fuentes, x_panel, ancho_panel, alto_ventana, filas, titulo, pie):
    dibujar_fondo_panel(ventana, x_panel, ancho_panel, alto_ventana)
    dibujar_encabezado(ventana, fuentes, x_panel, ancho_panel, titulo)
    dibujar_lista_jugadores(ventana, fuentes, x_panel, alto_ventana, filas)
    dibujar_pie_panel(ventana, fuentes, x_panel, ancho_panel, alto_ventana, pie)