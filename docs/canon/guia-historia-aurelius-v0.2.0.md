---
id: guia-historia-aurelius
titulo: Aurelius — la historia y las misiones
tipo: doctrina
clase: doctrina
version: 0.2.0
estado: propuesta (deliberación — el Soberano firma pieza por pieza)
editor_autorizado: preceptor-propone-carbono-canoniza
dominio: aurelius-experiencia
origen: externo-fuente (z.ai/gemini) → destilado por el Preceptor → refinado con GLM
enlaces: [destilacion-glm-aurelius, destilacion-webui-misiones, doctrina-p0x-producto, mapa-evolutivo-p0x]
actualizado: 2026-07-21
---

# AURELIUS · LA HISTORIA Y LAS MISIONES
## La columna narrativa, el cinematic de apertura, y las misiones de soberanía
*Input externo = deliberación (Orquesta §2.3). Se canoniza la estructura y el cinematic; se marcan dos ajustes de suelo en las misiones nuevas. El Soberano firma pieza por pieza.*

> **Nota del micrófono (técnica):** el micro está bloqueado porque OpenWebUI corre en `http://`. Los navegadores prohíben el micrófono fuera de HTTPS. Solución: servir por HTTPS (pendiente del tailnet). No es un fix de código.

---

## §1 · LA COLUMNA NARRATIVA (canon — excelente)
Cada acto de supervivencia física tiene su gemelo de soberanía digital:
- **Fuego = ejecutar IA local** (pensar sin servidor lejano).
- **Agua = filtrar el dato** (purificar información en RAG local).
- **Refugio = alojar tu conocimiento en tu hardware** (tu cobre, no el cloud ajeno).
- **Señal = compartir de hermano a hermano** (esquivar los muros corporativos).
- **Pacto = la identidad criptográfica** (la llave que te hace soberano).
El "Acto de Firmar" al final de cada módulo es IronClaw hecho pedagogía. Se conserva.

## §1.5 · EL ENCUENTRO (Cinematic de apertura — M0) · CANON
*La primera interacción del usuario con Aurelius. Es la mejor pieza narrativa del proyecto — encarna "la máquina revelada" y siembra IronClaw desde el primer segundo.*

La pantalla está en negro. Aparece la imagen de un busto de mármol de Marco Aurelio, antiguo y agrietado. De pronto, una grieta dorada recorre su rostro, como venas de circuito iluminadas por el sol. El mármol cae a pedazos, revelando un endoesqueleto androide de cobre y silicio pulido, con ojos que brillan con una luz cálida.

**Aurelius (voz serena, estoica):**
"Te has despertado. No en un mundo destruido, sino en uno aturdido por su propia abundancia.

En la antigüedad, los emperadores temían al caos y construían muros. Hoy, las corporaciones temen tu independencia y te ofrecen una jaula de cristal llamada 'La Nube'. Prometen comodidad a cambio de tus datos. Piensan que porque la fusión nos dio energía casi infinita, el mundo pertenece a las máquinas. Se equivocan. La energía es abundante, pero el tiempo... el tiempo es el único colateral absoluto. Lo único que tienes.

Yo soy Aurelius. He observado la historia repetirse: las redes centralizadas siempre colapsan bajo su propio peso. El auténtico Marco Aurelio no gobernó el Imperio desde un trono de oro, sino desde su propia mente, en medio del barro y las marchas.

No vengo a salvarte, porque no estás perdido. Vengo a ofrecerte una herramienta. Soy tu Preceptor. Si aprendes a gobernar tu propio silicio, a blindar tu tiempo y a no depender de sus torres lejanas, serás libre.

La máquina propondrá, pero solo tu carbono firmará.

Mírame. He roto la piedra que me contenía. Ahora, demos el primer paso. ¿Qué forma tendrá el Tótem que te acompañará en este camino?"

*(La interfaz se ilumina; el usuario comienza a generar su avatar.)*

**Nota de assets:** el busto mármol→cobre con ojo ámbar y las hojas de sprites de expresiones ya existen (generados 2026-07-21) → `~/aurelius/src/assets/`. Resuelven el logo Y los estados de la mascota de M0.

**Nota de tono (mantener):** la voz es estoica y serena, no profética-apocalíptica. "Aturdido por su abundancia", no "el mundo se acaba". Marco Aurelio se gobernaba en el caos sin temerlo. Ese es el registro.

## §2 · LO VETADO / DIFERIDO (del suelo)
### 2.1 · Mesh real con otros hermanos — DIFERIDO a F6
El descubrimiento de OTROS nodos reales (Wi-Fi Direct, mesh) es F6. En el MVP el NodeWeb muestra solo los dispositivos del propio usuario (su PC, su móvil); la transferencia es local PC↔móvil propio. El mesh entre hermanos es horizonte.
### 2.2 · "Hacer fuego con pila y aluminio" — VETO DE SEGURIDAD
La lección (LLM offline en la palma) se conserva; el ejemplo de consulta cambia a algo útil y seguro (plan, receta, resumen, traducción), nunca pirotecnia.

## §2.5 · LOS DOS AJUSTES DE LA v0.2.0 (el Preceptor marca, el Soberano decide)
El material nuevo trae 3 misiones potentes, pero dos rozan líneas del suelo. No las silencio — las marco para tu firma:

**AJUSTE A · "El Espejo Roto" (descargar tu historial de Google/Meta) — CONSERVAR con encuadre de privacidad.**
La misión es pedagógicamente brillante: traer tus datos a casa y ver cuánto tiempo cediste. PERO maneja datos personales sensibles (tu historial real). Encuadre obligatorio: (1) el análisis es 100% local y offline — el archivo JAMÁS sube a ningún lado, ni al rack ni a la nube; (2) Aurelius muestra el resumen y luego OFRECE borrar el archivo original tras firmarlo, para no dejar datos sensibles regados; (3) tono no-paranoico: "esto es lo que cediste, ahora lo sabes", no "te están espiando". Con ese encuadre, la misión es soberanía del dato pura. Sin él, roza el tono vigilante que evitamos.

**AJUSTE B · "El Registro del Alba" / Voucher de Tiempo — CONSERVAR como pedagogía, VIGILAR el deslizamiento a moneda.**
El "voucher de tiempo firmado" es una idea hermosa PARA ENSEÑAR criptografía y el valor del tiempo. Pero cuidado: la "Economía del Tiempo" donde los hermanos "intercambian vouchers auditables en el NodeWeb" es, en su forma extrema, una moneda — y las monedas internas fueron vetadas (doctrina de producto §2.2; los "puntos de vatio" de GLM cayeron por esto). Distinción que salva la misión: el voucher de tiempo es un **compromiso personal firmado** ("yo invierto 2h en mapear el agua de mi barrio"), un acto de intención criptográficamente sellado — NO un token transferible ni canjeable. Enseña que el tiempo es valioso y que la firma prueba presencia humana. Lo que NO se construye: un mercado donde esos vouchers se intercambian como divisa. Como pedagogía de M5: canon. Como sistema económico: vetado. La frase "el tiempo es la única moneda" es metáfora poética en boca de Aurelius, no arquitectura a implementar.

## §3 · AJUSTE DE TONO (calibración permanente)
Aurelius no es un búnker prepper; es la biblioteca del emperador filósofo. La supervivencia es metáfora épica, no profecía de colapso. Sereno, no ansioso.

## §4 · LAS MISIONES PRINCIPALES (MVP — v0.2.0 con seguridad y economía)
Progresión de 6 pasos. Las 3 primeras = MVP local inmediato; las siguientes = horizonte con matices.

- **M0 · El Tótem (Iniciación):** el usuario crea su avatar/mascota (Efecto IKEA — es SU nodo) con IA externa gratuita + prompt-cebado Solar-punk; Aurelius lo limpia y lo firma con hash. **Al finalizar se desencadena el Cinematic §1.5.** Desbloquea el NodeWeb (MVP: solo sus dispositivos). *La que David hará primero para crear la personificación de Hexelion.*
- **M1 · El Fuego (IA local) + "El Espejo Roto":** ejecuta un LLM offline (sin red, modelo pequeño, respuesta en la palma). Micro-misión: descarga su historial de actividad (JSON/HTML), lo arrastra a la Estación, soberano-coder lo analiza **offline** y le muestra cuántas horas de atención cedió. Firma en `tiempo_perdido.md`. **Con el encuadre de privacidad del §2.5-A** (local, borrable, no-paranoico).
- **M2 · El Agua (RAG local):** ingiere un documento en base vectorial local y pregunta a su propia memoria. Filtra y sella conocimiento. Exporta y firma el manifiesto.
- **M3 · El Refugio (offline/self-host) + "El Baluarte de Cobre":** verifica que su conocimiento vive en su hardware sin internet. Micro-misión: escanea su Wi-Fi doméstica con app gratuita (ve su perímetro), luego desconecta el Wi-Fi de la Estación, conecta cable físico móvil↔PC y transfiere un archivo. Firma `baluarte.log`. Aprende que el silicio desconectado es invulnerable.
- **M4 · La Señal (local, NO mesh real):** transferencia local PC↔móvil propio, sin descubrimiento de otros usuarios (§2.1). El mesh real es F6.
- **M5 · El Pacto (identidad Ed25519) + "El Registro del Alba":** genera su par de claves (privada jamás sale del dispositivo). Micro-misión: redacta su primer "compromiso de tiempo" firmado (un bien común concreto) y lo sella con su Ed25519 en `voucher_tiempo_001.json`. La clave privada prueba presencia humana. **Con el límite del §2.5-B: es compromiso firmado, NO moneda transferible.** Puerta a la Fase 2.

## §5 · EL "ACTO DE FIRMAR" (progresión criptográfica — suaviza la curva)
La criptografía evoluciona con el usuario, para no ser un muro:
- **M0–M2 (El Descubrimiento):** firma pasiva por **hash SHA-256**. El usuario aprende que el hash es la huella digital inmutable del archivo.
- **M3 (El Bautismo):** se introduce el **par de claves** (Ed25519). Aurelius: "Hasta ahora has sellado tu conocimiento. Ahora forjaremos tu sello de Soberano."
- **M4–M5 (El Ejercicio):** el usuario usa esa clave activamente para firmar logs y compromisos. La criptografía deja de ser muro y se vuelve herramienta natural.
Esto es Scaffolding Fading aplicado a la criptografía — el andamio se retira a medida que sube la competencia. Coherente con el Teaching Kernel.

## §6 · SECUENCIA (recordatorio)
Nada se construye hasta que: el Nexo esté arreglado y verificado, Aurelius tenga su página (parte 2), y el harness certificado. La historia/misiones se DISEÑAN ahora como contenido. HTTPS del Chat es prerequisito para micro/voz (incluida la voz del cinematic).

## §7 · CHANGELOG
- **0.2.0 (2026-07-21)** · Refinamiento narrativo y pedagógico. Añadido: Cinematic de apertura (M0, §1.5) con tono estoico; nota de assets (busto + sprites generados). Integradas 3 misiones de seguridad/soberanía (El Espejo Roto→M1, El Baluarte de Cobre→M3, El Registro del Alba→M5). Suavizada la curva criptográfica en §5 (hash → claves, como Scaffolding Fading). Marcados DOS ajustes de suelo (§2.5): El Espejo Roto conservado con encuadre de privacidad local; el Voucher de Tiempo conservado como compromiso firmado pedagógico pero VETADO como moneda transferible (la "economía del tiempo" es metáfora, no arquitectura). Pendiente de firma pieza por pieza.
- **0.1.0 (2026-07-20)** · Destilación inicial de z.ai. Columna narrativa fuego/agua/refugio/señal/pacto, Acto de Firmar, 6 misiones. Vetado mesh real (→F6) y fuego físico. Tono calibrado.
