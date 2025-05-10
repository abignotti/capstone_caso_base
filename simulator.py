# simulator.py  – bucle de 260 semanas
# --------------------------------------------------------------
from __future__ import annotations
from typing import List
import pandas as pd
import re

from entities import Aircraft, Motor

LEASE_PRICE = 70000
MAINT_WEEKS = 18
MAX_LIMIT = {
    "A319": 15500, "A320": 15500, "A321": 8000,
    "B767F": 14500, "B767J": 15500,
}

def base_family(code: str) -> str:
    """
    Devuelve la familia base:
      A319JJ  -> A319
      A3204C  -> A320
      A321LA  -> A321
      B767F-ABSA -> B767F
      B767J18    -> B767J
    """
    code_clean = re.sub(r"[^A-Za-z0-9]", "", code).upper()

    # A32x → 4 primeros (A319, A320, A321)
    if code_clean.startswith("A32"):
        return code_clean[:4]

    # B767  → capturar 'B767' + posible F o J
    if code_clean.startswith("B767"):
        return code_clean[:5] if len(code_clean) >= 5 else "B767"

    # fallback
    return code_clean[:4]

def compatible(m: Motor, ac: Aircraft) -> bool:
    """Un motor es compatible si pertenece a la misma categoría NB/WB."""
    return m.category == ac.category


def simulate(aircraft: List[Aircraft],
             inventory: List[Motor],
             weeks: int = 260) -> tuple[pd.DataFrame, dict]:

    costs = {"lease": 0}
    rows = []
    EPS = 1.0           # margen de seguridad de 1 ciclo

    for w in range(weeks):
        # 1) avanzar y detectar motores que superan límite (doble chequeo)
        motors_out = []
        for ac in aircraft:
            mot = ac.motor
            if mot is None:
                continue

            limit = MAX_LIMIT[base_family(ac.family)]

            # (a) ¿ya está sobre el límite?
            if mot.cycles >= limit - EPS:         #  <= margen
                motors_out.append(mot)
                mot.installed_on = None
                ac.motor = None
                continue

            # (b) ¿se pasaría si suma la semana completa?
            if mot.cycles + ac.cycles_per_week >= limit - EPS:
                motors_out.append(mot)            # también lo retiro preventivo
                mot.installed_on = None
                ac.motor = None
                continue

            # (c) caso normal: volar
            mot.cycles += ac.cycles_per_week


        # 2) enviar a mantenimiento
        for m in motors_out:
            m.weeks_left_maint = MAINT_WEEKS
            if m not in inventory:
                inventory.append(m)

        # 3) progresar mantenimiento y armar pool listo
        ready_pool = []
        for m in inventory:
            if m.weeks_left_maint > 0:
                m.weeks_left_maint -= 1
            if m.weeks_left_maint == 0 and m.installed_on is None:
                ready_pool.append(m)

        # 4) asignar motores faltantes
        for ac in [a for a in aircraft if a.motor is None]:
            mot = next((m for m in ready_pool if compatible(m, ac)), None)
            if mot:
                ready_pool.remove(mot)
            if mot in inventory:
                inventory.remove(mot)
            else:
                mot = Motor(id=f"LEASE-{w}-{len(inventory)}",
                            family=ac.family,
                            category=ac.category,
                            cycles=0,
                            is_leased=True)
                costs["lease"] += LEASE_PRICE
                inventory.append(mot)
            
            # --- Reset si cambia de familia base (A320 -> A321, B767F -> B767J) ---
            if base_family(mot.family) != base_family(ac.family):
                mot.cycles = 0                 # comienza “en cero” en la nueva familia
                mot.family = ac.family         # actualiza la etiqueta del motor

            mot.installed_on = ac.id
            ac.motor = mot

        # 5) registro semanal
        for ac in aircraft:
            rows.append({
                "week": w,
                "aircraft": ac.id,
                "motor": ac.motor.id,
                "is_leased": ac.motor.is_leased
            })

    return pd.DataFrame(rows), costs


if __name__ == "__main__":
    from loaders import load_fleet
    acs, inv = load_fleet("datos")
    df, c = simulate(acs, inv, weeks=10)
    print(df.head())
