# Captura la Bandera — CC8 2026

![Python](https://img.shields.io/badge/Python-3-blue?logo=python&logoColor=white)
![pygame](https://img.shields.io/badge/pygame-2.6-green?logo=python&logoColor=white)
![Protocolo](https://img.shields.io/badge/protocolo-v1.2-orange)
![Estado](https://img.shields.io/badge/estado-jugable-brightgreen)

Juego multijugador de Captura la Bandera para el curso de Redes (CC8), proyecto individual con arquitectura cliente/servidor sobre sockets TCP/UDP, siguiendo el [estándar de protocolo](docs/protocolo.md) acordado con la clase.

---

## Cómo ejecutar

Requiere Python 3 y pygame:

```bash
pip install pygame --break-system-packages
```

Desde la raíz del proyecto:

```bash
python3 main.py
```

Se abre un menú donde elegís **S** para modo servidor o **C** para modo cliente. El servidor necesita al menos 2 jugadores conectados antes de poder iniciar la partida (ENTER en su ventana).

---

## Características

| | |
|---|---|
| **Descubrimiento automático** | Broadcast UDP en el puerto 8888, con respaldo de conexión manual por IP. |
| **Autoridad del servidor** | Posiciones, captura de bandera y victoria se calculan en el servidor; el cliente solo envía intenciones. |
| **Ciclo completo de partida** | Lobby → cuenta regresiva → juego → victoria → regreso automático al lobby. |
| **Manejo de errores** | Validación de campos, tipos, fases y límites según los códigos del estándar de la clase. |
| **Interfaz gráfica** | Cliente y servidor en pygame, panel de jugadores en vivo y registro configurable para depurar. |

---

## Estructura del proyecto

```
src/
├── comun/      → protocolo, constantes y utilidades de dibujo compartidas
├── servidor/   → lógica de red, física del juego y ciclo de partida
└── cliente/    → red, interfaz y control del jugador
docs/           → bitácora de desarrollo, registro de prompts de IA y documentación del protocolo
```

---

## Documentación

- [Bitácora de desarrollo](docs/bitacora.md) — cronología del proyecto con decisiones y commits relevantes.
- [Registro de prompts de IA](docs/ia_prompts.md) — uso de inteligencia artificial durante el desarrollo.
- [Protocolo de comunicación](docs/protocolo.md) — cómo se logra la interoperabilidad con otros proyectos de la clase.