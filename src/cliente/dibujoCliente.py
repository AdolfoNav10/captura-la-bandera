import pygame
import threading
import random
from src.cliente import redCliente as rc
from src.comun import estilo as es

ANCHO_PANEL = 320

ancho_ventana = 0
alto_ventana = 0
lado_juego = 0
offset_x = 0
offset_y = 0
x_panel = 0

pantalla_actual = "nombre"
nombre_escrito = ""
ip_escrita = ""
servidores_encontrados = []
busqueda_terminada = False


def buscar_servidores():
    global servidores_encontrados, busqueda_terminada
    servidores_encontrados = rc.descubrir_servidores()
    busqueda_terminada = True


def iniciar_busqueda():
    global busqueda_terminada, pantalla_actual
    busqueda_terminada = False
    pantalla_actual = "buscando"
    hilo = threading.Thread(target=buscar_servidores)
    hilo.daemon = True
    hilo.start()


def conectar_a(ip, puerto):
    global pantalla_actual
    pantalla_actual = "conectando"
    hilo = threading.Thread(target=rc.conectar, args=(ip, puerto, nombre_escrito))
    hilo.daemon = True
    hilo.start()


def conectar_manual():
    global pantalla_actual
    pantalla_actual = "conectando"
    hilo = threading.Thread(target=rc.conectar_manual, args=(ip_escrita, nombre_escrito))
    hilo.daemon = True
    hilo.start()


def escalar_posicion(x, y):
    escala = lado_juego / rc.config_juego["map_size"]
    return offset_x + x * escala, offset_y + y * escala


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


def mapa_de_nombres():
    nombres = {}
    for jugador in rc.estado_cliente["lobby"]:
        nombres[jugador.get("id")] = str(jugador.get("name"))
    return nombres


def dibujar_caja_texto(ventana, fuente, contenido, centro_x, y):
    ancho_caja = 520
    alto_caja = 62
    x_caja = centro_x - ancho_caja / 2
    rectangulo = pygame.Rect(x_caja, y, ancho_caja, alto_caja)

    pygame.draw.rect(ventana, es.COLOR_PANEL, rectangulo, border_radius=10)
    pygame.draw.rect(ventana, es.COLOR_ARENA, rectangulo, 2, border_radius=10)

    imagen = fuente.render(contenido + "_", True, es.COLOR_TEXTO)
    ventana.blit(imagen, (x_caja + 20, y + 16))


def filas_del_panel():
    nombres = mapa_de_nombres()
    portador = rc.ultimo_state["flag"].get("owner")
    fase = rc.estado_cliente["fase"]

    if fase == "lobby":
        lista = []
        for jugador in rc.estado_cliente["lobby"]:
            lista.append({"id": jugador.get("id"), "name": str(jugador.get("name"))})
    else:
        lista = []
        for jugador in rc.ultimo_state["players"]:
            id_jugador = jugador.get("id")
            lista.append({"id": id_jugador, "name": nombres.get(id_jugador, str(id_jugador))})

    filas = []
    posicion = 0
    for jugador in lista:
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


def iniciar():
    global pantalla_actual, nombre_escrito, ip_escrita
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
    pygame.display.set_caption("Captura la Bandera")
    reloj = pygame.time.Clock()

    fuentes = {
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

    radio_jugador = max(6, int(rc.config_juego["player_radius"] * lado_juego / 1000))
    centro_x_juego = zona_juego / 2

    ultima_direccion_enviada = (0, 0)

    ejecutando = True
    while ejecutando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False

            if evento.type == pygame.KEYDOWN:

                if pantalla_actual == "nombre":
                    if evento.key == pygame.K_RETURN:
                        if nombre_escrito.strip() == "":
                            nombre_escrito = "Jugador" + str(random.randint(100, 999))
                        iniciar_busqueda()
                    elif evento.key == pygame.K_BACKSPACE:
                        nombre_escrito = nombre_escrito[:-1]
                    elif len(nombre_escrito) < 20 and evento.unicode != "" and evento.unicode.isprintable():
                        nombre_escrito = nombre_escrito + evento.unicode

                elif pantalla_actual == "lista":
                    if evento.key == pygame.K_r:
                        iniciar_busqueda()
                    if evento.key == pygame.K_m:
                        pantalla_actual = "ip"
                    if evento.key >= pygame.K_1 and evento.key <= pygame.K_9:
                        indice = evento.key - pygame.K_1
                        if indice < len(servidores_encontrados):
                            elegido = servidores_encontrados[indice]
                            conectar_a(elegido["ip"], elegido["tcp_port"])

                elif pantalla_actual == "ip":
                    if evento.key == pygame.K_RETURN:
                        if ip_escrita.strip() != "":
                            conectar_manual()
                    elif evento.key == pygame.K_ESCAPE:
                        pantalla_actual = "lista"
                    elif evento.key == pygame.K_BACKSPACE:
                        ip_escrita = ip_escrita[:-1]
                    elif evento.unicode in "0123456789.:":
                        ip_escrita = ip_escrita + evento.unicode

                elif pantalla_actual == "error":
                    if evento.key == pygame.K_r:
                        rc.estado_cliente["error"] = None
                        iniciar_busqueda()

                elif pantalla_actual == "juego":
                    if evento.key == pygame.K_SPACE:
                        rc.enviar_interact()

        if pantalla_actual == "buscando" and busqueda_terminada:
            pantalla_actual = "lista"

        if pantalla_actual == "conectando":
            if rc.estado_cliente["conectado"]:
                pantalla_actual = "juego"
            elif rc.estado_cliente["error"] is not None:
                pantalla_actual = "error"

        if pantalla_actual == "juego":
            if rc.estado_cliente["fase"] == "playing":
                direccion_actual = calcular_direccion_actual()
                if direccion_actual != ultima_direccion_enviada:
                    rc.enviar_input(direccion_actual[0], direccion_actual[1])
                    ultima_direccion_enviada = direccion_actual
            else:
                ultima_direccion_enviada = (0, 0)

        ventana.fill(es.COLOR_FONDO)

        if pantalla_actual == "nombre":
            es.dibujar_texto_centrado(ventana, fuentes["titulo"], "CAPTURA LA BANDERA", ancho_ventana / 2, alto_ventana * 0.20, es.COLOR_BANDERA)
            es.dibujar_texto_centrado(ventana, fuentes["normal"], "Escribe tu nombre", ancho_ventana / 2, alto_ventana * 0.38, es.COLOR_APAGADO)
            dibujar_caja_texto(ventana, fuentes["normal"], nombre_escrito, ancho_ventana / 2, alto_ventana * 0.44)
            es.dibujar_texto_centrado(ventana, fuentes["normal"], "ENTER para continuar", ancho_ventana / 2, alto_ventana * 0.58, es.COLOR_APAGADO)

        elif pantalla_actual == "buscando":
            es.dibujar_texto_centrado(ventana, fuentes["titulo"], "CAPTURA LA BANDERA", ancho_ventana / 2, alto_ventana * 0.20, es.COLOR_BANDERA)
            es.dibujar_texto_centrado(ventana, fuentes["grande"], "Buscando servidores...", ancho_ventana / 2, alto_ventana * 0.46, es.COLOR_ARENA)

        elif pantalla_actual == "lista":
            es.dibujar_texto_centrado(ventana, fuentes["titulo"], "SERVIDORES", ancho_ventana / 2, alto_ventana * 0.10, es.COLOR_ACENTO)

            if len(servidores_encontrados) == 0:
                es.dibujar_texto_centrado(ventana, fuentes["grande"], "No se encontro ningun servidor", ancho_ventana / 2, alto_ventana * 0.40, es.COLOR_TEXTO)
            else:
                y_fila = alto_ventana * 0.26
                numero = 1
                for servidor in servidores_encontrados:
                    texto_fila = str(numero) + ".   " + str(servidor["name"]) + "    -    " + str(servidor["players"]) + " jugadores    -    " + str(servidor["state"]) + "    -    " + servidor["ip"]
                    es.dibujar_texto_centrado(ventana, fuentes["normal"], texto_fila, ancho_ventana / 2, y_fila, es.COLOR_TEXTO)
                    y_fila = y_fila + 50
                    numero = numero + 1

            es.dibujar_texto_centrado(ventana, fuentes["normal"], "1-9 elegir      R buscar de nuevo      M escribir IP", ancho_ventana / 2, alto_ventana * 0.86, es.COLOR_APAGADO)

        elif pantalla_actual == "ip":
            es.dibujar_texto_centrado(ventana, fuentes["titulo"], "CONEXION MANUAL", ancho_ventana / 2, alto_ventana * 0.20, es.COLOR_ACENTO)
            es.dibujar_texto_centrado(ventana, fuentes["normal"], "IP del servidor (o IP:puerto)", ancho_ventana / 2, alto_ventana * 0.38, es.COLOR_APAGADO)
            dibujar_caja_texto(ventana, fuentes["normal"], ip_escrita, ancho_ventana / 2, alto_ventana * 0.44)
            es.dibujar_texto_centrado(ventana, fuentes["normal"], "ENTER conectar      ESC volver", ancho_ventana / 2, alto_ventana * 0.58, es.COLOR_APAGADO)

        elif pantalla_actual == "conectando":
            es.dibujar_texto_centrado(ventana, fuentes["grande"], "Conectando...", ancho_ventana / 2, alto_ventana * 0.46, es.COLOR_ARENA)

        elif pantalla_actual == "error":
            es.dibujar_texto_centrado(ventana, fuentes["grande"], "No se pudo conectar", ancho_ventana / 2, alto_ventana * 0.40, es.COLOR_ERROR)
            if rc.estado_cliente["error"] is not None:
                es.dibujar_texto_centrado(ventana, fuentes["normal"], rc.estado_cliente["error"], ancho_ventana / 2, alto_ventana * 0.50, es.COLOR_APAGADO)
            es.dibujar_texto_centrado(ventana, fuentes["normal"], "R  -  buscar de nuevo", ancho_ventana / 2, alto_ventana * 0.60, es.COLOR_TEXTO)

        elif pantalla_actual == "juego":
            es.dibujar_arena(ventana, offset_x, offset_y, lado_juego, rc.config_juego["map_size"], rc.config_juego["circle_radius"])

            fase = rc.estado_cliente["fase"]
            nombres = mapa_de_nombres()
            portador = rc.ultimo_state["flag"].get("owner")

            if fase == "playing" or fase == "finished":
                x_bandera, y_bandera = escalar_posicion(rc.ultimo_state["flag"]["x"], rc.ultimo_state["flag"]["y"])
                es.dibujar_bandera(ventana, int(x_bandera), int(y_bandera), max(4, radio_jugador // 2))

                posicion = 0
                for jugador in rc.ultimo_state["players"]:
                    id_jugador = jugador.get("id")
                    numero = es.numero_visible(id_jugador, posicion)
                    x_pantalla, y_pantalla = escalar_posicion(jugador["x"], jugador["y"])
                    es.dibujar_jugador(
                        ventana, fuentes["numero"],
                        int(x_pantalla), int(y_pantalla), radio_jugador,
                        es.color_de_jugador(numero), numero,
                        id_jugador == portador,
                        id_jugador == rc.estado_cliente["mi_id"],
                    )
                    posicion = posicion + 1

            if fase == "lobby":
                es.dibujar_texto_centrado(ventana, fuentes["grande"], "Esperando el inicio", centro_x_juego, alto_ventana * 0.44, es.COLOR_ARENA)

            if fase == "countdown" and rc.estado_cliente["countdown"] is not None:
                es.dibujar_texto_centrado(ventana, fuentes["normal"], "La partida comienza en", centro_x_juego, alto_ventana * 0.30, es.COLOR_TEXTO)
                es.dibujar_texto_centrado(ventana, fuentes["countdown"], str(rc.estado_cliente["countdown"]), centro_x_juego, alto_ventana * 0.36, es.COLOR_BANDERA)

            if fase == "finished":
                if rc.estado_cliente["ganador"] == rc.estado_cliente["mi_id"]:
                    es.dibujar_texto_centrado(ventana, fuentes["grande"], "HAS GANADO", centro_x_juego, 24, es.COLOR_BANDERA)
                else:
                    nombre_ganador = rc.estado_cliente["ganador_nombre"]
                    if nombre_ganador is None:
                        nombre_ganador = str(rc.estado_cliente["ganador"])
                    es.dibujar_texto_centrado(ventana, fuentes["grande"], "Gano " + nombre_ganador, centro_x_juego, 24, es.COLOR_TEXTO)

            if not rc.estado_cliente["conectado"] and fase != "finished":
                es.dibujar_texto_centrado(ventana, fuentes["grande"], "Se perdio la conexion", centro_x_juego, alto_ventana * 0.46, es.COLOR_ERROR)

            titulo_panel = "JUGADORES  (" + str(len(filas_del_panel())) + ")"
            pie = ["WASD mover    ESPACIO bandera", "Tu eres " + str(rc.estado_cliente["mi_nombre"])]
            es.dibujar_panel_jugadores(ventana, fuentes, x_panel, ANCHO_PANEL, alto_ventana, filas_del_panel(), titulo_panel, pie)

        pygame.display.flip()
        reloj.tick(60)

    pygame.quit()


if __name__ == "__main__":
    iniciar()