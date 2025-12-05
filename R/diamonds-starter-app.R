library(querychat)
library(ellmer)
library(ggplot2)

qc <- QueryChat$new(
  diamonds,
  "diamonds",
  client = ellmer::chat("claude/claude-sonnet-4-5")
)

# Generate a greeting with help from the LLM
greeting_text <- qc$generate_greeting()

# Save it
writeLines(greeting_text, "diamonds_greeting.md")

# Then use the saved greeting in your app
qc <- QueryChat$new(
  diamonds,
  "diamonds",
  client = ellmer::chat("claude/claude-sonnet-4-5"),
  greeting = "diamonds_greeting.md",
  data_description = "diamonds_data_description.md",
  extra_instructions = "diamonds_extra_instructions.md"
)

qc$app()
