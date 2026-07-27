

MOSTRAR_JSON = False
MOSTRAR_EVENTOS = True
MOSTRAR_ERRORES = True


def log_evento(*partes):
    if MOSTRAR_EVENTOS:
        print("[juego]", *partes)


def log_error(*partes):
    if MOSTRAR_ERRORES:
        print("[error]", *partes)


def log_json_enviado(texto):
    if MOSTRAR_JSON:
        print("[envia] ->", texto)


def log_json_recibido(texto):
    if MOSTRAR_JSON:
        print("[recibe] <-", texto)