import socket
from src.comun import protocolo as p

PUERTO_JUEGO = 8889


def conectar_a_servidor(ip_servidor):
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((ip_servidor, PUERTO_JUEGO))
    print("Conectado al servidor")

    mensaje_join = {
        "type": "join",
        "name": "Gaby",
    }
    p.enviar(cliente, mensaje_join)
    print("Se envio join al servidor")

    lector = p.LectorMensajes()

    while True:
        datos_recibidos = cliente.recv(1024)
        mensajes = lector.agregar_bytes(datos_recibidos)
        for mensaje in mensajes:
            print("Mensaje del servidor:", mensaje)


if __name__ == "__main__":
    conectar_a_servidor("localhost")