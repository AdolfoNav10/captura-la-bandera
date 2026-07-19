import socket
from src.comun import protocolo as p
from src.comun.constantes import CONFIG_DEFAULT

PUERTO_JUEGO = 8889


def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(("0.0.0.0", PUERTO_JUEGO))
    servidor.listen()
    print("Servidor esperando conexiones en el puerto", PUERTO_JUEGO)

    conexion, direccion = servidor.accept()
    print("Se conecto un cliente desde", direccion)

    lector = p.LectorMensajes()
    datos_recibidos = conexion.recv(1024)
    mensajes = lector.agregar_bytes(datos_recibidos)

    for mensaje in mensajes:
        print("Mensaje recibido:", mensaje)
        if mensaje["type"] == "join":
            respuesta = {
                "type": "welcome",
                "player_id": "p1",
                "config": CONFIG_DEFAULT,
            }
            p.enviar(conexion, respuesta)
            print("Se envio welcome al cliente")


if __name__ == "__main__":
    iniciar_servidor()