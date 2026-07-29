# Protocolo de comunicación

Este documento explica cómo este proyecto se comunica con las implementaciones de los demás compañeros de la clase. La referencia oficial es el documento *Estándar Protocolo CTF, CC8 2026*, que contiene el catálogo completo de mensajes, las constantes y los códigos de error. Acá se describe solamente cómo quedó implementado ese estándar y qué decisiones se tomaron para que la comunicación funcione entre proyectos distintos.

---

## 1. Los dos canales

La comunicación usa dos canales separados, cada uno con un propósito:

| Canal | Puerto | Uso | Motivo |
|---|---|---|---|
| UDP | 8888, fijo para toda la clase | Descubrir servidores | Permite preguntar a toda la red sin conocer ninguna dirección de antemano. |
| TCP | 8889, lo elige cada servidor | Toda la partida | Garantiza que los mensajes lleguen completos y en orden. |

Los dos canales usan el mismo formato: objetos JSON en UTF-8, con un campo `type` obligatorio que indica de qué mensaje se trata.

---

## 2. Cómo el cliente encuentra un servidor

El cliente no conoce la dirección del servidor, así que la descubre en tres pasos:

1. Envía por broadcast UDP el mensaje `{"type":"discover","v":1}` al puerto 8888. Se manda tanto a la dirección de broadcast general como a la de la propia subred, porque hay routers que no reenvían la primera.
2. Cada servidor activo responde directamente al remitente con un `server_info`, donde incluye su nombre, el puerto TCP donde escucha, su fase actual y cuántos jugadores tiene.
3. El cliente junta todas las respuestas durante dos segundos y muestra la lista de servidores encontrados para que el usuario elija uno.

La dirección del servidor no viaja dentro del mensaje. El cliente la saca de la dirección de origen del paquete UDP que recibió, como indica el estándar.

### Conexión manual

El broadcast no siempre funciona. Hay redes que lo bloquean y las conexiones por VPN no lo transportan. Por eso el cliente permite escribir la dirección del servidor a mano. En ese caso envía el mismo `discover`, pero dirigido solo a esa dirección, para averiguar el puerto TCP antes de conectarse. También acepta el formato `dirección:puerto` para saltarse el descubrimiento.

Esta opción fue necesaria en varias de las pruebas con compañeros, donde el broadcast no llegó.

---

## 3. Delimitación de mensajes

Este es el punto más delicado de la comunicación y una causa frecuente de incompatibilidad entre proyectos.

TCP no entrega mensajes, entrega un flujo continuo de bytes. Dos mensajes enviados por separado pueden llegar pegados en una sola lectura, y un mensaje puede llegar partido en dos. Por eso el estándar define que cada mensaje TCP es un JSON en una sola línea terminado en salto de línea, y que el receptor debe acumular los bytes en un buffer, cortar en cada salto de línea y guardar lo que sobre para la lectura siguiente.

En este proyecto esa regla está en un solo lugar, la clase `LectorMensajes` del módulo común, por la que pasan todos los datos entrantes del servidor y del cliente. Tenerla concentrada evita que la lógica se repita y se desincronice entre los dos lados.

Los datagramas UDP son la excepción: viajan completos en un solo paquete y no llevan salto de línea. Enviarlo es un error. Durante las pruebas, un compañero con validación estricta rechazaba las respuestas justamente por eso.

---

## 4. Secuencia de una partida

```
descubrimiento → lobby → cuenta regresiva → juego → fin de partida → lobby
```

| Fase | Qué pasa | Mensajes |
|---|---|---|
| Lobby | Los jugadores se unen y esperan. El servidor confirma cada entrada y publica la lista actualizada. | `join`, `welcome`, `lobby` |
| Cuenta regresiva | El anfitrión inicia la partida. Se avisa el tiempo restante y ya no entran jugadores nuevos. | `countdown` |
| Juego | El servidor simula el mundo y lo replica 20 veces por segundo. Los clientes envían solo intenciones. | `start`, `input`, `interact`, `state` |
| Fin | Se anuncia el ganador, se muestra el resultado unos segundos y todos vuelven al lobby sin reconectarse. | `game_over`, `lobby` |

El orden importa. Un cliente que reciba estado del juego antes de la señal de inicio puede rechazarlo por estar fuera de secuencia, así que el servidor envía primero el `start` y recién después cambia su fase interna.

---

## 5. Autoridad del servidor

Todo el estado oficial de la partida vive en el servidor. Esta decisión es la que permite que implementaciones escritas en lenguajes distintos jueguen la misma partida en igualdad de condiciones.

| El cliente envía | El servidor decide |
|---|---|
| Intención de movimiento (`-1`, `0` o `1` por eje) | La posición de cada jugador |
| Intención de interactuar con la bandera | Si la captura o el robo son válidos según la distancia |
| | Quién gana y cuándo termina la partida |

El cliente nunca envía coordenadas ni declara victorias. Solo comunica qué quiere hacer y dibuja lo que el servidor le informa. Un cliente modificado no puede teletransportarse ni proclamarse ganador porque esos datos no se aceptan.

---

## 6. Decisiones para la interoperabilidad

Estas son las medidas que se tomaron para que el proyecto conviva con implementaciones ajenas:

**Lectura tolerante.** Los campos desconocidos se ignoran y un mensaje de tipo no reconocido no corta la conexión. Un compañero que envíe información adicional no rompe este proyecto.

**Flexible al recibir, estricto al enviar.** Los datagramas UDP se aceptan con o sin salto de línea final, pero al enviarlos se cumple la norma al pie de la letra.

**Precisión numérica acotada.** Las posiciones se envían redondeadas a un decimal. La precisión completa de punto flotante era rechazada por validadores estrictos de otros proyectos.

**Validación completa de entrada.** Todo mensaje entrante se revisa en campos, tipos, valores y fase antes de modificar cualquier estado. Si algo no cumple, se responde con el código de error correspondiente y el estado del juego queda intacto.

**Resistencia a desconexiones.** Si un cliente se cae, se lo retira de la partida, la bandera vuelve al centro en caso de que la llevara, y los demás siguen jugando.

---

## 7. Verificación

La conformidad se comprobó en tres niveles:

1. **Local**, con servidor y clientes en la misma máquina, para validar la lógica del juego.
2. **Con netcat**, enviando mensajes armados a mano por TCP y UDP. Al ser una herramienta ajena al proyecto, confirma que el servidor cumple el estándar y no solo que se entiende consigo mismo.
3. **Con compañeros**, conectando implementaciones escritas en otros lenguajes. Este nivel mostró incompatibilidades que las pruebas locales no podían detectar y motivó varias de las decisiones de la sección anterior.

---

