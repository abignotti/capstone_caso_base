import pandas as pd
from pathlib import Path
from loaders import load_fleet            # para obtener ciclos/semana y familia
from simulator import base_family, MAX_LIMIT, MAINT_WEEKS, LEASE_PRICE

DATA_DIR     = Path("datos")
SCHEDULE_CSV = "base_schedule.csv"

# -------------------------------------------------------------------------
# 1) Leer el calendario generado por el simulador
# -------------------------------------------------------------------------
cal = pd.read_csv(SCHEDULE_CSV)

# -------------------------------------------------------------------------
# 2) Verificar disponibilidad (mismo nº de aviones cada semana)
# -------------------------------------------------------------------------
rows_per_week = cal.groupby("week").size()
assert rows_per_week.nunique() == 1, "Al menos un avión quedó sin motor alguna semana."
N_AVIONS = rows_per_week.iloc[0]

# -------------------------------------------------------------------------
# 3) Unicidad de (aircraft, week) y (motor, week)
# -------------------------------------------------------------------------
assert cal.duplicated(["week", "aircraft"]).sum() == 0, "Avión repetido en la misma semana."
assert cal.duplicated(["week", "motor"]).sum() == 0, "Motor montado en >1 avión la misma semana."

# -------------------------------------------------------------------------
# 4) Diccionarios de apoyo: ciclos/semana y familia por avión
# -------------------------------------------------------------------------
aircraft_list, _ = load_fleet(DATA_DIR)
cycles_map  = {ac.id: ac.cycles_per_week for ac in aircraft_list}
family_map  = {ac.id: ac.family          for ac in aircraft_list}

# -------------------------------------------------------------------------
# 5) Recorrer por motor y comprobar límites y duración de mantención
# -------------------------------------------------------------------------
violations = 0         # motores que superan el límite de ciclos
maint_err  = 0         # gaps < MAINT_WEEKS

for motor_id, g in cal.groupby("motor"):
    g_sorted = g.sort_values("week")

    # diferencias entre semanas consecutivas -> huecos de mantención
    week_gaps = g_sorted["week"].diff().fillna(1).astype(int) - 1

    cycles = 0
    for (_, row), gap in zip(g_sorted.iterrows(), week_gaps):
        if gap > 0:                         # motor estuvo fuera
            if gap < MAINT_WEEKS-1:
                maint_err += 1
            cycles = 0                      # se reinicia tras mantención

        # sumar ciclos volados esta semana
        cycles += cycles_map[row["aircraft"]]
        fam     = base_family(family_map[row["aircraft"]])
        limit   = MAX_LIMIT[fam]

        if cycles > limit + 1e-6:
            print(f"Motor {motor_id} superó límite en semana {row['week']}: "
            f"{cycles:.1f} > {limit} (avión {row['aircraft']})")
            violations += 1
            break

# -------------------------------------------------------------------------
# 6) Resultados
# -------------------------------------------------------------------------
print(f"✔ Disponibilidad: {N_AVIONS} aviones cada semana")
print("✔ Sin duplicados de avión ni motor")
print(f"✘ Motores que superan límite: {violations}")
print(f"✘ Gaps < {MAINT_WEEKS} semanas de mantención: {maint_err}")

leasing_weeks = cal["is_leased"].sum()
print(f"Semanas de arriendo: {leasing_weeks}  →  Costo ${leasing_weeks * LEASE_PRICE:,.0f}")