# src/cliente/dibujoCliente.py

import pygame

from src.cliente import redCliente as rc
from src.cliente import estado_interfaz as ui
from src.cliente import entrada_teclado as teclado
from src.cliente import pantallas

ANCHO_PANEL = 320


def calcular_geometria():
    info_pantalla = pygame.display.Info()
    ancho = info_pantalla.current_w - 60
    alto = info_pantalla.current_h - 100

    zona_juego = ancho - ANCHO_PANEL
    lado = min(zona_juego, alto) - 60

    ui.geometria["ancho"] = ancho
    ui.geometria["alto"] = alto
    ui.geometria["lado"] = lado
    ui.geometria["offset_x"] = (zona_juego - lado) // 2
    ui.geometria["offset_y"] = (alto - lado) // 2
    ui.geometria["x_panel"] = ancho - ANCHO_PANEL
    ui.geometria["centro_juego"] = zona_juego / 2
    ui.geometria["radio_jugador"] = max(6, int(rc.config_juego["player_radius"] * lado / 1000))


def crear_fuentes():
    return {
        "titulo": pygame.font.SysFont(None, 86),
        "normal": pygame.font.SysFont(None, 38),
        "grande": pygame.font.SysFont(None, 62),
        "countdown": pygame.font.SysFont(None, 190),
        "titulo_panel": pygame.font.SysFont(None, 34),
        "panel": pygame.font.SysFont(None, 30),
        "numero_panel": pygame.font.SysFont(None, 22),
        "numero": pygame.font.SysFont(None, 24),
        "pie": pygame.font.SysFont(None, 24),
    }


def enviar_movimiento(ultima_direccion):
    if ui.pantalla_actual() != "juego":
        return ultima_direccion

    if rc.estado_cliente["fase"] != "playing":
        return (0, 0)

    direccion_actual = teclado.calcular_direccion_actual()

    if direccion_actual != ultima_direccion:
        rc.enviar_input(direccion_actual[0], direccion_actual[1])
        return direccion_actual

    return ultima_direccion


def iniciar():
    pygame.init()
    calcular_geometria()

    ventana = pygame.display.set_mode((ui.geometria["ancho"], ui.geometria["alto"]))
    pygame.display.set_caption("Captura la Bandera")

    reloj = pygame.time.Clock()
    fuentes = crear_fuentes()
    ultima_direccion = (0, 0)

    ejecutando = True
    while ejecutando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False

            if evento.type == pygame.KEYDOWN:
                teclado.manejar_tecla(evento)

        ui.actualizar_transiciones()
        ultima_direccion = enviar_movimiento(ultima_direccion)

        pantallas.dibujar_pantalla_actual(ventana, fuentes)
        pygame.display.flip()
        reloj.tick(60)

    pygame.quit()


if __name__ == "__main__":
    iniciar()