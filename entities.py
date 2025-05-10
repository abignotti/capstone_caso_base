from dataclasses import dataclass

@dataclass
class Motor:
    id: str
    family: str              # “A320”, “A321”, “B767F”, …
    category: str            # “NB” o “WB”   ← NUEVO
    cycles: int = 0
    weeks_left_maint: int = 0
    installed_on: str | None = None
    is_leased: bool = False
    is_bought: bool = False

MAX_LIMIT = {  # límites por family
    "A319": 15500, "A320": 15500, "A321": 8000,
    "B767F": 14500, "B767J": 15500,
}

@dataclass
class Aircraft:
    id: str
    family: str              # “A321”, “B767F”, …
    category: str            # “NB” o “WB”
    cycles_per_week: float
    motor: Motor | None = None

    def tick_week(self) -> bool:
        """Avanza una semana y devuelve True si el motor pasó el límite."""
        if not self.motor or self.motor.weeks_left_maint > 0:
            return False
        self.motor.cycles += self.cycles_per_week
        limit = MAX_LIMIT[self.family]
        return self.motor.cycles >= limit


if __name__ == "__main__":
    m = Motor(id="M1", family="A321", category="NB",
              installed_on="CC-ABC")
    ac = Aircraft(id="CC-ABC", family="A321", category="NB",
                  cycles_per_week=350, motor=m)

    for w in range(25):
        reached = ac.tick_week()
        print(f"Semana {w:2d}: ciclos={m.cycles:5.0f}, sobre_limite={reached}")

