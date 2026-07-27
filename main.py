import pygame
from src.comun import estilo as es


def menu_principal():
    pygame.init()
    ventana = pygame.display.set_mode((760, 440))
    pygame.display.set_caption("Captura la Bandera")

    fuente_titulo = pygame.font.SysFont(None, 72)
    fuente = pygame.font.SysFont(None, 42)
    fuente_pie = pygame.font.SysFont(None, 26)

    modo_elegido = None

    ejecutando = True
    while ejecutando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_s:
                    modo_elegido = "servidor"
                    ejecutando = False
                if evento.key == pygame.K_c:
                    modo_elegido = "cliente"
                    ejecutando = False

        ventana.fill(es.COLOR_FONDO)

        es.dibujar_bandera(ventana, 380, 130, 12)
        es.dibujar_texto_centrado(ventana, fuente_titulo, "CAPTURA LA BANDERA", 380, 175, es.COLOR_BANDERA)
        es.dibujar_texto_centrado(ventana, fuente, "S   -   Modo servidor", 380, 270, es.COLOR_ARENA)
        es.dibujar_texto_centrado(ventana, fuente, "C   -   Modo cliente", 380, 320, es.COLOR_ACENTO)
        es.dibujar_texto_centrado(ventana, fuente_pie, "CC8 2026   -   protocolo v1", 380, 390, es.COLOR_APAGADO)

        pygame.display.flip()

    pygame.quit()
    return modo_elegido


if __name__ == "__main__":
    modo = menu_principal()

    if modo == "servidor":
        from src.servidor import dibujoServidor
        dibujoServidor.iniciar()

    if modo == "cliente":
        from src.cliente import dibujoCliente
        dibujoCliente.iniciar()