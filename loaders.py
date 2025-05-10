from __future__ import annotations

import re
from pathlib import Path
from typing import Tuple, List

import pandas as pd

from entities import Motor, Aircraft

###############################################################################
# utilidades internas
###############################################################################

def _norm(s: str) -> str:
    """Normaliza un string quitando espacios/guiones y a mayúsculas."""
    return re.sub(r"[^A-Za-z0-9]", "", str(s)).upper()


def _family_from_code(code: str) -> str:
    """Extrae familia base: A319JJ → A319, B767F-ABSA → B767F."""
    m = re.match(r"([A-Z0-9]+)", code.upper())
    return m.group(1) if m else code.upper()

###############################################################################
# función principal
###############################################################################

def load_fleet(data_dir: str | Path) -> Tuple[List[Aircraft], List[Motor]]:
    """Devuelve (lista_aviones, lista_motores_iniciales)."""
    data_dir = Path(data_dir)

    ###########################################################################
    # Narrow‑Body
    ###########################################################################
    cycles_nb  = pd.read_csv(data_dir / "Cycles_operations_NB.csv")
    status_nb  = pd.read_csv(data_dir / "Fleet_status_NB.csv")

    # map "A320JJ"  -> cycles per week (c/día × 7)
    cycles_map_nb = (cycles_nb.assign(cpw=lambda d: d["Cycles per day"] * 7)
                               .set_index("Aircraft")["cpw"].to_dict())

    aircraft_list: List[Aircraft] = []
    motor_inventory: List[Motor]  = []

    for idx, row in status_nb.iterrows():
        type_code   = row["fleet_operator"]          # A320JJ, A319LP, …
        family      = _family_from_code(type_code)    # A320, A319, …
        cpw         = cycles_map_nb[type_code]        # ciclos/semana según CSV

        ac_id = f"{row['matricula']}_AV"             # matrícula real preferida
        ac = Aircraft(id=ac_id,
                      family=family,
                      category="NB",
                      cycles_per_week=cpw)

        mot = Motor(id=row["matricula"],
                    family=family,
                    category="NB",
                    cycles=row["cycles"],
                    installed_on=ac.id)

        ac.motor = mot
        aircraft_list.append(ac)
        motor_inventory.append(mot)

    ###########################################################################
    # Wide‑Body
    ###########################################################################
    cycles_wb = pd.read_csv(data_dir / "Operations_cycles_WB.csv")
    status_wb = pd.read_csv(data_dir / "Fleet_status_WB.csv")

    # normalizar nombres en cycles_wb para que coincidan con Operation sin guiones/espacios
    cycles_wb["key"] = cycles_wb["Aircraft"].map(_norm)
    cycles_map_wb = (cycles_wb.assign(cpw=lambda d: d["Value"] * 7)
                               .set_index("key")["cpw"].to_dict())

    for idx, row in status_wb.iterrows():
        type_raw   = row["Operation"]                 # "B767F-ABSA" etc.
        type_key   = _norm(type_raw)                  # "B767FABSA"
        family     = _family_from_code(type_raw)      # "B767F" / "B767J"
        cpw        = cycles_map_wb[type_key]

        ac_id = f"{row['matricula']}_AV"
        ac = Aircraft(id=ac_id,
                      family=family,
                      category="WB",
                      cycles_per_week=cpw)

        mot = Motor(id=row["matricula"],
                    family=family,
                    category="WB",
                    cycles=row["cycles"],
                    installed_on=ac.id)

        ac.motor = mot
        aircraft_list.append(ac)
        motor_inventory.append(mot)

    return aircraft_list, motor_inventory

###############################################################################
# pequeño test rápido
###############################################################################
if __name__ == "__main__":
    ac_list, mot_list = load_fleet("datos")
    print("Aviones:", len(ac_list))
    print("Motores iniciales:", len(mot_list))
    print(ac_list)