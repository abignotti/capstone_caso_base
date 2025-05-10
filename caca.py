import pandas as pd
df = pd.read_csv("base_schedule.csv")

av = df[df["aircraft"] == "EC-4815-90_AV"]
print(av[["week", "motor", "is_leased"]].head(30))
