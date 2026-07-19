import json


def enviar(sock, mensaje: dict):
    texto = json.dumps(mensaje) + "\n"
    sock.sendall(texto.encode("utf-8"))


class LectorMensajes:
    def __init__(self):
        self._buffer = b""

    def agregar_bytes(self, datos: bytes) -> list[dict]:
        self._buffer += datos
        mensajes = []

        while b"\n" in self._buffer:
            linea, self._buffer = self._buffer.split(b"\n", 1)
            if linea.strip():
                try:
                    mensaje = json.loads(linea.decode("utf-8"))
                    mensajes.append(mensaje)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass

        return mensajes