# src/servidor/fisica.py

import math
import random
from src.comun.constantes import CONFIG_DEFAULT, SPAWN_RADIO_MIN, SPAWN_RADIO_MAX


def centro_del_mapa():
    return CONFIG_DEFAULT["map_size"] / 2


def radio_de_victoria():
    return CONFIG_DEFAULT["circle_radius"] + CONFIG_DEFAULT["player_radius"]


def calcular_distancia(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def distancia_al_centro(x, y):
    centro = centro_del_mapa()
    return calcular_distancia(x, y, centro, centro)


def esta_dentro_del_circulo(x, y):
    return distancia_al_centro(x, y) <= radio_de_victoria()


def generar_posicion_inicial():
    centro = centro_del_mapa()
    angulo = random.uniform(0, 2 * math.pi)
    radio = random.uniform(SPAWN_RADIO_MIN, SPAWN_RADIO_MAX)

    x = centro + radio * math.cos(angulo)
    y = centro + radio * math.sin(angulo)
    return x, y


def normalizar_direccion(dir_x, dir_y):
    if dir_x != 0 and dir_y != 0:
        factor = math.sqrt(2)
        return dir_x / factor, dir_y / factor

    return dir_x, dir_y


def limitar_al_mapa(valor):
    radio_jugador = CONFIG_DEFAULT["player_radius"]
    limite_mapa = CONFIG_DEFAULT["map_size"]

    if valor < radio_jugador:
        return radio_jugador

    if valor > limite_mapa - radio_jugador:
        return limite_mapa - radio_jugador

    return valor


def mover_jugador(datos_jugador, segundos_transcurridos):
    velocidad = CONFIG_DEFAULT["speed"]

    dir_x, dir_y = normalizar_direccion(datos_jugador["dir_x"], datos_jugador["dir_y"])

    nueva_x = datos_jugador["x"] + dir_x * velocidad * segundos_transcurridos
    nueva_y = datos_jugador["y"] + dir_y * velocidad * segundos_transcurridos

    datos_jugador["x"] = limitar_al_mapa(nueva_x)
    datos_jugador["y"] = limitar_al_mapa(nueva_y)