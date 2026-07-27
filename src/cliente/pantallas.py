# src/cliente/pantallas.py

import pygame

from src.comun import estilo as es
from src.cliente import redCliente as rc
from src.cliente import estado_interfaz as ui


def dibujar_caja_texto(ventana, fuente, contenido, centro_x, y):
    ancho_caja = 520
    alto_caja = 62
    x_caja = centro_x - ancho_caja / 2
    rectangulo = pygame.Rect(x_caja, y, ancho_caja, alto_caja)

    pygame.draw.rect(ventana, es.COLOR_PANEL, rectangulo, border_radius=10)
    pygame.draw.rect(ventana, es.COLOR_ARENA, rectangulo, 2, border_radius=10)

    imagen = fuente.render(contenido + "_", True, es.COLOR_TEXTO)
    ventana.blit(imagen, (x_caja + 20, y + 16))


def mapa_de_nombres():
    nombres = {}

    for jugador in rc.estado_cliente["lobby"]:
        nombres[jugador.get("id")] = str(jugador.get("name"))

    return nombres


def lista_para_el_panel():
    nombres = mapa_de_nombres()

    if rc.estado_cliente["fase"] == "lobby":
        lista = []
        for jugador in rc.estado_cliente["lobby"]:
            lista.append({"id": jugador.get("id"), "name": str(jugador.get("name"))})
        return lista

    lista = []
    for jugador in rc.ultimo_state["players"]:
        id_jugador = jugador.get("id")
        lista.append({"id": id_jugador, "name": nombres.get(id_jugador, str(id_jugador))})

    return lista


def filas_del_panel():
    portador = rc.ultimo_state["flag"].get("owner")
    filas = []
    posicion = 0

    for jugador in lista_para_el_panel():
        numero = es.numero_visible(jugador["id"], posicion)
        filas.append({
            "numero": numero,
            "nombre": jugador["name"],
            "color": es.color_de_jugador(numero),
            "es_portador": jugador["id"] == portador,
            "es_mio": jugador["id"] == rc.estado_cliente["mi_id"],
        })
        posicion = posicion + 1

    return filas


def pantalla_nombre(ventana, fuentes):
    centro_x = ui.geometria["ancho"] / 2
    alto = ui.geometria["alto"]

    es.dibujar_texto_centrado(ventana, fuentes["titulo"], "CAPTURA LA BANDERA", centro_x, alto * 0.20, es.COLOR_BANDERA)
    es.dibujar_texto_centrado(ventana, fuentes["normal"], "Escribe tu nombre", centro_x, alto * 0.38, es.COLOR_APAGADO)
    dibujar_caja_texto(ventana, fuentes["normal"], ui.interfaz["nombre"], centro_x, alto * 0.44)
    es.dibujar_texto_centrado(ventana, fuentes["normal"], "ENTER para continuar", centro_x, alto * 0.58, es.COLOR_APAGADO)


def pantalla_buscando(ventana, fuentes):
    centro_x = ui.geometria["ancho"] / 2
    alto = ui.geometria["alto"]

    es.dibujar_texto_centrado(ventana, fuentes["titulo"], "CAPTURA LA BANDERA", centro_x, alto * 0.20, es.COLOR_BANDERA)
    es.dibujar_texto_centrado(ventana, fuentes["grande"], "Buscando servidores...", centro_x, alto * 0.46, es.COLOR_ARENA)


def pantalla_lista(ventana, fuentes):
    centro_x = ui.geometria["ancho"] / 2
    alto = ui.geometria["alto"]
    servidores = ui.interfaz["servidores"]

    es.dibujar_texto_centrado(ventana, fuentes["titulo"], "SERVIDORES", centro_x, alto * 0.10, es.COLOR_ACENTO)

    if len(servidores) == 0:
        es.dibujar_texto_centrado(ventana, fuentes["grande"], "No se encontro ningun servidor", centro_x, alto * 0.40, es.COLOR_TEXTO)
    else:
        y_fila = alto * 0.26
        numero = 1

        for servidor in servidores:
            texto_fila = str(numero) + ".   " + str(servidor["name"])
            texto_fila = texto_fila + "    -    " + str(servidor["players"]) + " jugadores"
            texto_fila = texto_fila + "    -    " + str(servidor["state"])
            texto_fila = texto_fila + "    -    " + servidor["ip"]

            es.dibujar_texto_centrado(ventana, fuentes["normal"], texto_fila, centro_x, y_fila, es.COLOR_TEXTO)
            y_fila = y_fila + 50
            numero = numero + 1

    es.dibujar_texto_centrado(ventana, fuentes["normal"], "1-9 elegir      R buscar de nuevo      M escribir IP", centro_x, alto * 0.86, es.COLOR_APAGADO)


def pantalla_ip(ventana, fuentes):
    centro_x = ui.geometria["ancho"] / 2
    alto = ui.geometria["alto"]

    es.dibujar_texto_centrado(ventana, fuentes["titulo"], "CONEXION MANUAL", centro_x, alto * 0.20, es.COLOR_ACENTO)
    es.dibujar_texto_centrado(ventana, fuentes["normal"], "IP del servidor (o IP:puerto)", centro_x, alto * 0.38, es.COLOR_APAGADO)
    dibujar_caja_texto(ventana, fuentes["normal"], ui.interfaz["ip"], centro_x, alto * 0.44)
    es.dibujar_texto_centrado(ventana, fuentes["normal"], "ENTER conectar      ESC volver", centro_x, alto * 0.58, es.COLOR_APAGADO)


def pantalla_conectando(ventana, fuentes):
    centro_x = ui.geometria["ancho"] / 2
    alto = ui.geometria["alto"]

    es.dibujar_texto_centrado(ventana, fuentes["grande"], "Conectando...", centro_x, alto * 0.46, es.COLOR_ARENA)


def pantalla_error(ventana, fuentes):
    centro_x = ui.geometria["ancho"] / 2
    alto = ui.geometria["alto"]

    es.dibujar_texto_centrado(ventana, fuentes["grande"], "No se pudo conectar", centro_x, alto * 0.40, es.COLOR_ERROR)

    if rc.estado_cliente["error"] is not None:
        es.dibujar_texto_centrado(ventana, fuentes["normal"], rc.estado_cliente["error"], centro_x, alto * 0.50, es.COLOR_APAGADO)

    es.dibujar_texto_centrado(ventana, fuentes["normal"], "R  -  buscar de nuevo", centro_x, alto * 0.60, es.COLOR_TEXTO)


def dibujar_jugadores(ventana, fuentes):
    portador = rc.ultimo_state["flag"].get("owner")
    posicion = 0

    for jugador in rc.ultimo_state["players"]:
        id_jugador = jugador.get("id")
        numero = es.numero_visible(id_jugador, posicion)
        x_pantalla, y_pantalla = ui.escalar_posicion(jugador["x"], jugador["y"])

        es.dibujar_jugador(
            ventana, fuentes["numero"],
            int(x_pantalla), int(y_pantalla), ui.geometria["radio_jugador"],
            es.color_de_jugador(numero), numero,
            id_jugador == portador,
            id_jugador == rc.estado_cliente["mi_id"],
        )
        posicion = posicion + 1


def dibujar_mundo(ventana, fuentes):
    x_bandera, y_bandera = ui.escalar_posicion(rc.ultimo_state["flag"]["x"], rc.ultimo_state["flag"]["y"])
    tamano_bandera = max(4, ui.geometria["radio_jugador"] // 2)
    es.dibujar_bandera(ventana, int(x_bandera), int(y_bandera), tamano_bandera)

    dibujar_jugadores(ventana, fuentes)


def dibujar_aviso_de_fase(ventana, fuentes):
    centro_x = ui.geometria["centro_juego"]
    alto = ui.geometria["alto"]
    fase = rc.estado_cliente["fase"]

    if fase == "lobby":
        es.dibujar_texto_centrado(ventana, fuentes["grande"], "Esperando el inicio", centro_x, alto * 0.44, es.COLOR_ARENA)

    if fase == "countdown" and rc.estado_cliente["countdown"] is not None:
        es.dibujar_texto_centrado(ventana, fuentes["normal"], "La partida comienza en", centro_x, alto * 0.30, es.COLOR_TEXTO)
        es.dibujar_texto_centrado(ventana, fuentes["countdown"], str(rc.estado_cliente["countdown"]), centro_x, alto * 0.36, es.COLOR_BANDERA)

    if fase == "finished":
        if rc.estado_cliente["ganador"] == rc.estado_cliente["mi_id"]:
            es.dibujar_texto_centrado(ventana, fuentes["grande"], "HAS GANADO", centro_x, 24, es.COLOR_BANDERA)
        else:
            nombre_ganador = rc.estado_cliente["ganador_nombre"]
            if nombre_ganador is None:
                nombre_ganador = str(rc.estado_cliente["ganador"])
            es.dibujar_texto_centrado(ventana, fuentes["grande"], "Gano " + nombre_ganador, centro_x, 24, es.COLOR_TEXTO)

    if not rc.estado_cliente["conectado"] and fase != "finished":
        es.dibujar_texto_centrado(ventana, fuentes["grande"], "Se perdio la conexion", centro_x, alto * 0.46, es.COLOR_ERROR)


def pantalla_juego(ventana, fuentes):
    es.dibujar_arena(
        ventana,
        ui.geometria["offset_x"], ui.geometria["offset_y"], ui.geometria["lado"],
        rc.config_juego["map_size"], rc.config_juego["circle_radius"],
    )

    fase = rc.estado_cliente["fase"]

    if fase == "playing" or fase == "finished":
        dibujar_mundo(ventana, fuentes)

    dibujar_aviso_de_fase(ventana, fuentes)

    filas = filas_del_panel()
    titulo_panel = "JUGADORES  (" + str(len(filas)) + ")"
    pie = ["WASD mover    ESPACIO bandera", "Tu eres " + str(rc.estado_cliente["mi_nombre"])]

    es.dibujar_panel_jugadores(
        ventana, fuentes,
        ui.geometria["x_panel"], ui.geometria["ancho"] - ui.geometria["x_panel"], ui.geometria["alto"],
        filas, titulo_panel, pie,
    )


def dibujar_pantalla_actual(ventana, fuentes):
    ventana.fill(es.COLOR_FONDO)
    pantalla = ui.pantalla_actual()

    if pantalla == "nombre":
        pantalla_nombre(ventana, fuentes)
    elif pantalla == "buscando":
        pantalla_buscando(ventana, fuentes)
    elif pantalla == "lista":
        pantalla_lista(ventana, fuentes)
    elif pantalla == "ip":
        pantalla_ip(ventana, fuentes)
    elif pantalla == "conectando":
        pantalla_conectando(ventana, fuentes)
    elif pantalla == "error":
        pantalla_error(ventana, fuentes)
    elif pantalla == "juego":
        pantalla_juego(ventana, fuentes)