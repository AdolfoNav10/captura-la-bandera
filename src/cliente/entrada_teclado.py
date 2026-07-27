
# src/cliente/entrada_teclado.py

import pygame
import random

from src.cliente import redCliente as rc
from src.cliente import estado_interfaz as ui


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


def tecla_en_nombre(evento):
    if evento.key == pygame.K_RETURN:
        if ui.interfaz["nombre"].strip() == "":
            ui.interfaz["nombre"] = "Jugador" + str(random.randint(100, 999))
        ui.iniciar_busqueda()
        return

    if evento.key == pygame.K_BACKSPACE:
        ui.interfaz["nombre"] = ui.interfaz["nombre"][:-1]
        return

    if len(ui.interfaz["nombre"]) < 20 and evento.unicode != "" and evento.unicode.isprintable():
        ui.interfaz["nombre"] = ui.interfaz["nombre"] + evento.unicode


def tecla_en_lista(evento):
    if evento.key == pygame.K_r:
        ui.iniciar_busqueda()
        return

    if evento.key == pygame.K_m:
        ui.ir_a("ip")
        return

    if evento.key >= pygame.K_1 and evento.key <= pygame.K_9:
        indice = evento.key - pygame.K_1
        servidores = ui.interfaz["servidores"]

        if indice < len(servidores):
            elegido = servidores[indice]
            ui.conectar_a(elegido["ip"], elegido["tcp_port"])


def tecla_en_ip(evento):
    if evento.key == pygame.K_RETURN:
        if ui.interfaz["ip"].strip() != "":
            ui.conectar_manual()
        return

    if evento.key == pygame.K_ESCAPE:
        ui.ir_a("lista")
        return

    if evento.key == pygame.K_BACKSPACE:
        ui.interfaz["ip"] = ui.interfaz["ip"][:-1]
        return

    if evento.unicode in "0123456789.:":
        ui.interfaz["ip"] = ui.interfaz["ip"] + evento.unicode


def tecla_en_error(evento):
    if evento.key == pygame.K_r:
        rc.estado_cliente["error"] = None
        ui.iniciar_busqueda()


def tecla_en_juego(evento):
    if evento.key == pygame.K_SPACE:
        rc.enviar_interact()


def manejar_tecla(evento):
    pantalla = ui.pantalla_actual()

    if pantalla == "nombre":
        tecla_en_nombre(evento)
    elif pantalla == "lista":
        tecla_en_lista(evento)
    elif pantalla == "ip":
        tecla_en_ip(evento)
    elif pantalla == "error":
        tecla_en_error(evento)
    elif pantalla == "juego":
        tecla_en_juego(evento)