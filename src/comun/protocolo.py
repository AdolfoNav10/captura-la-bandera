import json

from src.comun.constantes import MENSAJE_MAXIMO
from src.comun import registro


def enviar(sock, mensaje: dict):
    texto = json.dumps(mensaje)
    registro.log_json_enviado(texto)
    sock.sendall((texto + "\n").encode("utf-8"))


class LectorMensajes:
    def __init__(self):
        self._buffer = b""
        self.hubo_json_invalido = False
        self.mensaje_muy_grande = False

    def agregar_bytes(self, datos: bytes) -> list[dict]:
        self._buffer += datos

        if len(self._buffer) > MENSAJE_MAXIMO:
            self._buffer = b""
            self.mensaje_muy_grande = True
            return []

        mensajes = []

        while b"\n" in self._buffer:
            linea, self._buffer = self._buffer.split(b"\n", 1)

            if linea.endswith(b"\r"):
                linea = linea[:-1]

            if linea.strip():
                try:
                    texto = linea.decode("utf-8")
                    registro.log_json_recibido(texto)
                    mensajes.append(json.loads(texto))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    self.hubo_json_invalido = True

        return mensajes