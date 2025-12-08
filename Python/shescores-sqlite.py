from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine
from querychat import QueryChat
import pandas as pd

load_dotenv()  # Loads key from the .env file

# From results_with_scorers.csv, create a SQLite database named shescores.db
df_path = Path(__file__).parent.parent / "data/results_with_scorers.csv"

df = pd.read_csv(df_path)
# Create the SQLite database and store the DataFrame in it
# Save database in top-level /data directory
df.to_sql(
    "results_with_scorers",
    con=create_engine(
        "sqlite:///" + str(Path(__file__).parent.parent / "data/shescores.db")
    ),
    if_exists="replace",
    index=False,
)

# Custom files for SheScores
shescores_greeting = Path(__file__).parent / "shescores_greeting.md"
shescores_data_description = Path(__file__).parent / "shescores_data_description.md"
shescores_extra_instructions = Path(__file__).parent / "shescores_extra_instructions.md"

# Now create a QueryChat instance to interact with the database
db_path = Path(__file__).parent.parent / "data/shescores.db"
engine = create_engine(f"sqlite:///{db_path}")

qc = QueryChat(
    engine,
    "results_with_scorers",
    client="anthropic/claude-sonnet-4-5",
    greeting=shescores_greeting,
    data_description=shescores_data_description,
    extra_instructions=shescores_extra_instructions,
)

app = qc.app()
