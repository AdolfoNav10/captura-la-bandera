import socket

PUERTO_JUEGO = 8889


def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(("0.0.0.0", PUERTO_JUEGO))
    servidor.listen()
    print("Servidor esperando conexiones en el puerto", PUERTO_JUEGO)

    conexion, direccion = servidor.accept()
    print("Se conecto un cliente desde", direccion)


if __name__ == "__main__":
    iniciar_servidor()