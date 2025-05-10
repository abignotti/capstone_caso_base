from loaders import load_fleet
from simulator import simulate

aircraft, motors = load_fleet("datos")
calendar, costs  = simulate(aircraft, motors)
p = costs["lease"]

calendar.to_csv("base_schedule.csv", index=False)
print(f"Costo total leasing 5 años: ${p:,.0f}")

  
