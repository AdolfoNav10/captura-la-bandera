import socket

PUERTO_JUEGO = 8889


def conectar_a_servidor(ip_servidor):
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((ip_servidor, PUERTO_JUEGO))
    print("Conectado al servidor")
    return cliente


if __name__ == "__main__":
    conectar_a_servidor("localhost")