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
    rows  = []
    EPS   = 1.0
    lease_counter = 0            # ids únicos: LEASE-w-n

    for w in range(weeks):

        # ----------------------------------------------------------
        # 1) Avanzar ciclos y retirar motores que llegan (o llegarían)
        #    al límite esta semana
        # ----------------------------------------------------------
        motors_out = []
        for ac in aircraft:
            mot = ac.motor
            if mot is None:
                continue

            limit = MAX_LIMIT[base_family(ac.family)]
            if mot.cycles >= limit - EPS \
               or mot.cycles + ac.cycles_per_week >= limit - EPS:
                motors_out.append(mot)
                mot.installed_on = None
                ac.motor = None
            else:
                mot.cycles += ac.cycles_per_week

        # 2) Enviar a mantenimiento --------------------------------
        for m in motors_out:
            m.weeks_left_maint = MAINT_WEEKS
            if m not in inventory:
                inventory.append(m)

        # 3) Progresar mantenimiento y construir ready_pool --------
        ready_pool = []
        for m in inventory:
            if m.weeks_left_maint > 0:
                m.weeks_left_maint -= 1
            if m.weeks_left_maint == 0 and m.installed_on is None:
                m.cycles = 0
                ready_pool.append(m)

        # 4) Asignar motores faltantes -----------------------------
        for ac in [a for a in aircraft if a.motor is None]:
            mot = next((m for m in ready_pool if compatible(m, ac)), None)
            if mot:
                ready_pool.remove(mot)
                inventory.remove(mot)          # sale del inventario
            else:
                # crear motor arrendado válido solo 1 semana
                mot = Motor(id=f"LEASE-{w}-{lease_counter}",
                            family=ac.family,
                            category=ac.category,
                            cycles=0,
                            is_leased=True)
                lease_counter += 1
                costs["lease"] += LEASE_PRICE   # cobrar UNA semana

            # reset de familia si cambia
            if base_family(mot.family) != base_family(ac.family):
                mot.cycles = 0
                mot.family = ac.family

            mot.installed_on = ac.id
            ac.motor = mot

        # 5) Registrar calendario (antes de devolver arrendados) ---
        for ac in aircraft:
            rows.append({
                "week": w,
                "aircraft": ac.id,
                "motor": ac.motor.id if ac.motor else "NONE",
                "is_leased": ac.motor.is_leased if ac.motor else False,
                "cycles"   : round(ac.motor.cycles, 1) if ac.motor else 0
            })

        # 6) Devolver arrendados al proveedor ----------------------
        for ac in aircraft:
            if ac.motor and ac.motor.is_leased:
                ac.motor.installed_on = None
                ac.motor = None


    return pd.DataFrame(rows), costs 



if __name__ == "__main__":
    from loaders import load_fleet
    acs, inv = load_fleet("datos")
    df, c = simulate(acs, inv, weeks=10)
    print(df.head())
