from dotenv import load_dotenv
from seaborn import load_dataset
from querychat import QueryChat
from pathlib import Path

load_dotenv()  # Loads key from the .env file

diamonds = load_dataset("diamonds")
qc = QueryChat(diamonds, "diamonds", client="anthropic/claude-sonnet-4-5")

# Generate a greeting with help from the LLM
greeting_text = qc.generate_greeting()

# Save it
with open("diamonds_greeting.md", "w") as f:
    f.write(greeting_text)

# Then use the saved greeting in your app
qc = QueryChat(
    diamonds,
    "diamonds",
    client="anthropic/claude-sonnet-4-5",
    greeting=Path(__file__).parent / "diamonds_greeting.md",
    data_description=Path(__file__).parent / "diamonds_data_description.md",
    extra_instructions=Path(__file__).parent / "diamonds_extra_instructions.md",
)

app = qc.app()
