library(querychat)
library(DBI)

# From results_with_scorers.csv, create a SQLite database named shescores.db
results_with_scorers <- read.csv("data/results_with_scorers.csv")

# Create a connection to a new SQLite database
# Save database in top-level /data directory
con <- dbConnect(RSQLite::SQLite(), "data/shescores.db")

# Write the data frame to a table named results_with_scorers
dbWriteTable(
  con,
  "results_with_scorers",
  results_with_scorers,
  overwrite = TRUE
)

# Now create a QueryChat instance to interact with the database
qc <- QueryChat$new(
  con,
  "results_with_scorers",
  client = "claude/claude-sonnet-4-5",
  greeting = "shescores_greeting.md",
  data_description = "shescores_data_description.md",
  extra_instructions = "shescores_extra_instructions.md"
)

qc$app()
