library(shiny)
library(bslib)
library(DT)
library(querychat)
library(ellmer)
library(ggplot2)

# ===============================
# Setup
# ===============================
# 1. Initialize QueryChat with custom files
qc <- QueryChat$new(
  diamonds,
  "diamonds",
  client = "claude/claude-sonnet-4-5",
  greeting = "diamonds_greeting.md",
  data_description = "diamonds_data_description.md",
  extra_instructions = "diamonds_extra_instructions.md"
)

# ===============================
# UI
# ===============================
ui <- page_sidebar(
  title = "Diamonds Explorer",
  # 2. QueryChat sidebar UI component
  sidebar = qc$sidebar(),
  card(
    card_header("SQL Query"),
    verbatimTextOutput("sql_query")
  ),
  card(
    card_header(textOutput("title")),
    DT::DTOutput("data_table")
  )
)

# ===============================
# Server
# ===============================
server <- function(input, output, session) {
  # 3. QueryChat server component
  vals <- qc$server()

  # 3. Display generated SQL query
  output$sql_query <- renderText({
    if (vals$sql() == "") {
      return("SELECT * FROM diamonds;")
    }
    vals$sql()
  })

  # 4. Display data table based on user query
  output$data_table <- DT::renderDT({
    vals$df()
  })

  # 5. Dynamic title based on user query
  output$title <- renderText({
    if (!isTruthy(vals$title())) {
      return("Diamonds Data")
    }
    vals$title()
  })
}

shinyApp(ui, server)
