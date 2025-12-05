from shiny import App, render, ui
from dotenv import load_dotenv
from seaborn import load_dataset
from querychat import QueryChat
from pathlib import Path

load_dotenv()  # Loads key from the .env file

# ===============================
# Setup
# ===============================
# 1. Initialize QueryChat with custom files
diamonds = load_dataset("diamonds")
diamonds_greeting = Path(__file__).parent / "diamonds_greeting.md"
diamonds_data_description = Path(__file__).parent / "diamonds_data_description.md"
diamonds_extra_instructions = Path(__file__).parent / "diamonds_extra_instructions.md"

qc = QueryChat(
    diamonds,
    "diamonds",
    client="anthropic/claude-sonnet-4-5",
    greeting=diamonds_greeting,
    data_description=diamonds_data_description,
    extra_instructions=diamonds_extra_instructions,
)

# ===============================
# UI
# ===============================
app_ui = ui.page_sidebar(
    # 2. QueryChat sidebar UI component
    qc.sidebar(),
    ui.card(
        ui.card_header("SQL Query"),
        ui.output_text_verbatim("sql_output"),
        fill=True,
    ),
    ui.card(
        ui.card_header(ui.output_text("title")),
        ui.output_data_frame("data_table"),
        fill=True,
    ),
    fillable=True,
    theme=ui.Theme.from_brand(__file__),
)


# ===============================
# Server
# ===============================
def server(input, output, session):
    # 3. QueryChat server component
    vals = qc.server()

    # 4. Use the filtered/sorted data frame reactively
    @render.data_frame
    def data_table():
        return vals.df()

    @render.text
    def title():
        return vals.title() or "Diamonds"

    # 5. Display the generated SQL query
    @render.text
    def sql_output():
        return vals.sql() or "SELECT * FROM diamonds;"


app = App(app_ui, server)
