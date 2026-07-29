# Registro de prompts de IA

**Herramienta utilizada:** Claude (Anthropic), vía la interfaz de chat de claude.ai.

Este documento recoge las consultas más representativas realizadas durante el desarrollo, organizadas por etapa. El uso de la herramienta se orientó a resolver dudas de diseño, validar decisiones contra el estándar de la clase y diagnosticar problemas de interoperabilidad. Las respuestas obtenidas no se transcriben aquí: el código resultante vive en el repositorio y está referenciado por commit en [`bitacora.md`](bitacora.md). El foco de este documento es el proceso de razonamiento seguido.

---

## 1. Planificación inicial

| Consulta | Resultado |
|---|---|
| ¿Qué conviene tener resuelto antes de empezar a programar, considerando que el proyecto depende de un protocolo acordado con toda la clase? | Se definió un orden de trabajo previo al código: confirmar el cupo de lenguaje y librería en la hoja de la clase, crear el repositorio para que la cronología de Git arrancara desde el día uno, y ubicar el documento de constantes del profesor. |
| ¿Cómo convendría dividir el desarrollo en etapas para que cada una sea verificable antes de pasar a la siguiente? | Hoja de ruta en seis etapas (protocolo, conexión, movimiento, reglas, descubrimiento y blindaje), cada una con su propio criterio de "terminada" y su prueba asociada. |

---

## 2. Diseño del protocolo

| Consulta | Resultado |
|---|---|
| ¿Por qué el estándar exige acumular los bytes en un buffer en lugar de leer un mensaje por cada lectura del socket? | Comprensión del problema de framing en TCP: los mensajes pueden llegar pegados o partidos, lo que justifica la clase `LectorMensajes` y su corte por salto de línea. |
| ¿Qué diferencia hay entre el manejo de mensajes en TCP y en UDP según el estándar? | Confirmación de que el salto de línea aplica solo a TCP, ya que cada datagrama UDP llega completo. Esta distinción resultó clave más adelante para corregir un error de interoperabilidad. |

---

## 3. Lógica del juego y sincronización

| Consulta | Resultado |
|---|---|
| ¿En qué momento debe asignarse la posición inicial de cada jugador, y por qué el mensaje de estado repite la misma posición si nadie se ha movido? | Distinción entre la asignación de spawn, que ocurre una sola vez por jugador, y el ciclo de estado, que replica el mundo 20 veces por segundo independientemente de si hubo cambios. |
| ¿Cómo se puede verificar que la comunicación cumple el estándar y no solo que funciona entre mis propios programas? | Adopción de una estrategia de pruebas en tres niveles: local, con netcat como verificador neutral ajeno al proyecto, y con la implementación de un compañero. |

---

## 4. Fases de partida y manejo de errores

| Consulta | Resultado |
|---|---|
| Si omitiera los mensajes de cuenta regresiva e inicio, ¿qué riesgo habría frente a clientes de otros proyectos que sí los implementen? | Decisión de implementar el ciclo de fases completo, al identificar que un cliente ajeno podría quedarse esperando indefinidamente la señal de inicio. |
| ¿Cuáles de los errores del catálogo del estándar representan mayor riesgo para la estabilidad del servidor? | Priorización por severidad: primero los que podían detener el servidor por completo (desconexiones abruptas, mensajes recibidos antes del `join`) y luego las validaciones de campos y límites. |

---

## 5. Diagnóstico de interoperabilidad

| Consulta | Resultado |
|---|---|
| Un compañero recibe la respuesta de descubrimiento pero nunca abre la conexión de juego. ¿Cómo determino en qué punto exacto del flujo se corta? | Metodología de diagnóstico por capas: verificación de alcance de red, prueba del puerto TCP de forma aislada y observación del tráfico entrante con `tcpdump` para confirmar si los paquetes llegaban a la máquina. |
| Al comparar mi implementación con la de un compañero escrita en C#, ¿qué diferencias de formato podrían hacer que su validador rechace mis mensajes? | Análisis comparado de ambas implementaciones que descartó el código como causa y orientó la búsqueda hacia la configuración de red y el formato exacto de los datagramas. |
| Su validador rechaza mi mensaje de estado indicando que las posiciones admiten como máximo un decimal. ¿De dónde proviene esa diferencia? | Identificación de que las posiciones se enviaban con la precisión completa de punto flotante de Python. Se aplicó redondeo a un decimal conforme al estándar. |
| Ante un rechazo de mensaje entre dos implementaciones distintas, ¿cómo se determina objetivamente de qué lado está el incumplimiento? | Contraste del comportamiento observado contra el texto del estándar, que permitió confirmar que el envío de saltos de línea en datagramas UDP era propio y corregirlo en cliente y servidor. |

---

## 6. Revisión de conformidad con el estándar v1.2

| Consulta | Resultado |
|---|---|
| El estándar de la clase se actualizó a una versión más estricta. ¿Qué puntos de mi implementación dejaron de cumplirlo? | Auditoría completa que identificó cinco desviaciones: el campo de estado del servidor fuera de los valores permitidos, códigos de error en minúsculas, movimiento diagonal sin normalizar, condición de victoria sin exigir la transición dentro-fuera, y falta de notificación al lobby tras una desconexión. |

---

## 7. Organización del código

| Consulta | Resultado |
|---|---|
| ¿Cómo podría reorganizar los módulos para que cada archivo tenga una sola responsabilidad y sea más fácil de estudiar? | Propuesta de separación en módulos por responsabilidad: física, estado de partida y ciclo de partida del lado del servidor; estado de interfaz, pantallas y entrada de teclado del lado del cliente. |
| ¿En qué orden conviene leer los archivos del proyecto para entender el flujo completo de un mensaje? | Orden de lectura por capas: protocolo base, servidor, cliente y capa visual, siguiendo el recorrido de un mensaje desde que se envía hasta que se dibuja. |

---

## 8. Documentación

| Consulta | Resultado |
|---|---|
| ¿Cuál es la mejor forma de documentar el proyecto de modo que la cronología quede respaldada por el historial de Git? | Decisión de mantener la documentación en Markdown dentro del repositorio, con cada entrada de la bitácora enlazada a los commits que la respaldan, en lugar de un documento externo sin trazabilidad. |