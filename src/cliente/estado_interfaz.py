# src/cliente/estado_interfaz.py

import threading
from src.cliente import redCliente as rc

interfaz = {
    "pantalla": "nombre",
    "nombre": "",
    "ip": "",
    "servidores": [],
    "busqueda_terminada": False,
}

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


def ir_a(pantalla):
    interfaz["pantalla"] = pantalla


def pantalla_actual():
    return interfaz["pantalla"]


def buscar_servidores():
    interfaz["servidores"] = rc.descubrir_servidores()
    interfaz["busqueda_terminada"] = True


def iniciar_busqueda():
    interfaz["busqueda_terminada"] = False
    ir_a("buscando")

    hilo = threading.Thread(target=buscar_servidores)
    hilo.daemon = True
    hilo.start()


def conectar_a(ip, puerto):
    ir_a("conectando")

    hilo = threading.Thread(target=rc.conectar, args=(ip, puerto, interfaz["nombre"]))
    hilo.daemon = True
    hilo.start()


def conectar_manual():
    ir_a("conectando")

    hilo = threading.Thread(target=rc.conectar_manual, args=(interfaz["ip"], interfaz["nombre"]))
    hilo.daemon = True
    hilo.start()


def actualizar_transiciones():
    pantalla = pantalla_actual()

    if pantalla == "buscando" and interfaz["busqueda_terminada"]:
        ir_a("lista")
        return

    if pantalla == "conectando":
        if rc.estado_cliente["conectado"]:
            ir_a("juego")
            return

        if rc.estado_cliente["error"] is not None:
            ir_a("error")


def escalar_posicion(x, y):
    escala = geometria["lado"] / rc.config_juego["map_size"]
    x_pantalla = geometria["offset_x"] + x * escala
    y_pantalla = geometria["offset_y"] + y * escala
    return x_pantalla, y_pantalla