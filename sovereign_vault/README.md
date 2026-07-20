# Sovereign Vault

Artefactos **firmados** de las misiones del Camino Hexelion. Su contenido es del
**Soberano** (el usuario): **local, borrable**. Nada de aquí sube a ningún servidor.

Cada misión guarda aquí lo que el usuario creó y selló con su propia mano — porque
*la máquina propone, el carbono firma* (IronClaw).

```
M1_Espejo_Roto/     · M1 «El Fuego» + «El Espejo Roto» → tiempo_perdido.md (+ .sig.json)
M3_Baluarte_Cobre/  · M3 «El Refugio» + «El Baluarte de Cobre» → baluarte.log (+ .sig.json)
M5_Registro_Alba/   · M5 «El Pacto» + «El Registro del Alba» → voucher_tiempo_001.json
```

## El Acto de Firmar — progresión (§5 del canon)
- **M0–M2 (El Descubrimiento):** firma pasiva por **hash SHA-256** (`scripts/firmar_artefacto.py`).
  Prueba **integridad** (la huella inmutable del archivo), no autoría.
- **M3 (El Bautismo):** se introduce el **par de claves Ed25519** — la firma con clave
  (`scripts/firmar_con_clave.py`, aún no creado) prueba **autoría/presencia humana**.
- **M4–M5 (El Ejercicio):** el usuario firma logs y compromisos con su clave.

El andamio criptográfico se retira a medida que sube la competencia (Scaffolding Fading).
