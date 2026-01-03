from shiny import App, render, ui
from dotenv import load_dotenv
from querychat import QueryChat
from pathlib import Path
import pandas as pd
import plotly.express as px
from shinywidgets import output_widget, render_widget
import numpy as np

load_dotenv()  # Loads key from the .env file

# ===============================
# Setup
# ===============================
# read in data
# note that for demo purposes this is in a top-level folder
# normally, you would have this inside the folder that contains app.py
results_with_scorers = pd.read_csv(
    Path(__file__).parent.parent / "data/results_with_scorers.csv"
)

results_with_scorers["date"] = pd.to_datetime(results_with_scorers["date"])

results_with_scorers = results_with_scorers[
    (results_with_scorers["tournament"] != "Friendly")
    & (results_with_scorers["date"] >= "2000-01-01")
]

# 1. Initialize QueryChat with custom files
shescores_greeting = Path(__file__).parent / "shescores_greeting.md"
shescores_data_description = Path(__file__).parent / "shescores_data_description.md"
shescores_extra_instructions = Path(__file__).parent / "shescores_extra_instructions.md"

qc = QueryChat(
    results_with_scorers,
    "results_with_scorers",
    client="anthropic/claude-sonnet-4-5",
    greeting=shescores_greeting,
    data_description=shescores_data_description,
    extra_instructions=shescores_extra_instructions,
)

# ===============================
# UI
# ===============================
app_ui = ui.page_sidebar(
    qc.sidebar(),
    ui.layout_columns(
        ui.value_box(title="Top scoring country", value=ui.output_text("top_country")),
        ui.value_box(
            "Top scorer",
            ui.output_text("top_scorer"),
            ui.output_text("top_scorer_missing"),
        ),
        ui.value_box(title="Total countries", value=ui.output_text("total_countries")),
    ),
    ui.br(),
    ui.layout_columns(
        ui.card(output_widget("map"), min_height="500px"),
        ui.card(output_widget("overview"), min_height="500px"),
    ),
    ui.br(),
    ui.layout_columns(
        ui.card(
            ui.output_data_frame("results_table"),
            min_height="600px",
        )
    ),
    title="She Scores ⚽️: Women's International Soccer Matches",
    fillable=False,
    theme=ui.Theme.from_brand(__file__),
)


# ===============================
# Server
# ===============================
def server(input, output, session):
    # Reactive filtered data based on query
    filtered_data = qc.server()

    @render.text
    def top_country():
        df = filtered_data.df()
        if df.empty:
            return "No matches found"

        # --- home teams ---
        home = (
            df.groupby(["date", "home_team", "tournament"])
            .agg(
                country=("home_team", "first"),
                matches=("tournament", lambda x: x.nunique()),
                goals=("home_score", "first"),
                country_flag=("country_flag_home", "first"),
            )
            .reset_index(drop=True)
        )

        # --- away teams ---
        away = (
            df.groupby(["date", "away_team", "tournament"])
            .agg(
                country=("away_team", "first"),
                matches=("tournament", lambda x: x.nunique()),
                goals=("away_score", "first"),
                country_flag=("country_flag_away", "first"),
            )
            .reset_index(drop=True)
        )

        # combine home + away rows
        combined = pd.concat([home, away], ignore_index=True)

        # final summarisation
        top_country = (
            combined.groupby("country")
            .agg(
                matches=("matches", "sum"),
                goals=("goals", "sum"),
                country_flag=("country_flag", "first"),
            )
            .reset_index()
            .sort_values("goals", ascending=False)
            .head(1)
        )

        # equivalent of paste0(country, country_flag)
        result_string = (
            top_country["country"].iloc[0] + top_country["country_flag"].iloc[0]
        )

        return result_string

    @render.text
    def top_scorer():
        df = filtered_data.df()
        if df.empty or df["scorer"].notna().sum() == 0:
            return "No scorers found"

        top_scorer = (
            df[df["scorer"].notna()]
            .assign(
                country_flag=lambda x: np.where(
                    x["team"] == x["home_team"],
                    x["country_flag_home"],
                    x["country_flag_away"],
                )
            )
            .groupby(["scorer", "country_flag"])
            .size()
            .reset_index(name="goals")
            .sort_values("goals", ascending=False)
            .head(1)
        )

        result_string = (
            top_scorer["scorer"].iloc[0] + " " + top_scorer["country_flag"].iloc[0]
        )

        return result_string

    @render.text
    def top_scorer_missing():
        df = filtered_data.df()
        if df.empty:
            return ""

        missing = df["scorer"].isna().sum()
        total = len(df)
        missing_scorer_pct = missing / total * 100

        result_string = (
            "Missing scorer data: " + str(round(missing_scorer_pct, 2)) + "%"
        )

        return result_string

    @render.text
    def total_countries():
        df = filtered_data.df()
        if df.empty:
            return "0"

        total_countries = (
            df[["home_team", "away_team"]]
            .melt(value_name="country")
            .drop_duplicates(subset=["country"])
            .shape[0]
        )

        return total_countries

    @render_widget
    def overview():
        df = filtered_data.df()
        if df.empty:
            return px.scatter(title="No matches available for selected filters")

        overview_df = (
            df.groupby(df["date"].dt.year)
            .size()
            .reset_index(name="match_count")
            .rename(columns={"date": "year"})
        )

        fig = px.line(
            overview_df,
            x="year",
            y="match_count",
            title="Matches over time",
            labels={"year": "", "match_count": ""},
            markers=True,
        )

        fig.update_traces(
            line=dict(width=3, color="#0f0437"),
            marker=dict(size=6, color="white", line=dict(width=2, color="#5470C6")),
        )

        fig.update_layout(
            font=dict(family="Oswald, sans-serif", size=12, color="#343A40"),
            title=dict(font=dict(size=22)),
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                showgrid=False,
                zeroline=False,
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="lightgrey",
                zeroline=False,
            ),
        )

        return fig

    @render_widget
    def map():
        df = filtered_data.df()

        # drop missing coordinates
        df = df.dropna(subset=["latitude", "longitude"]).copy()

        # add year column
        df["year"] = pd.to_datetime(df["date"]).dt.year.astype(str)

        # group rows like your original code:
        grouped = (
            df.groupby(["tournament", "latitude", "longitude", "city"])["year"]
            .apply(lambda x: ", ".join(sorted(x.unique())))
            .reset_index()
            .rename(columns={"year": "years"})
        )

        # popup text equivalent
        grouped["hover_text"] = (
            "<b>"
            + grouped["tournament"]
            + "</b><br>"
            + grouped["city"]
            + "<br>"
            + "Years: "
            + grouped["years"]
        )

        fig = px.scatter_map(
            grouped,
            lat="latitude",
            lon="longitude",
            hover_name="tournament",
            hover_data={},
            custom_data=["hover_text"],
            zoom=1,
            height=600,
        )

        # Use a good base map
        fig.update_layout(
            autosize=True,
            mapbox_style="carto-positron",
        )

        fig.update_traces(
            hovertemplate="%{customdata[0]}<extra></extra>",
            cluster=dict(enabled=True),
            # football look
            marker=dict(
                size=20,
                symbol="circle",
                color="#5d923f",
            ),
        )

        return fig

    @render.data_frame
    def results_table():
        df = filtered_data.df()
        if df.empty:
            return pd.DataFrame()

        def summarize_scorers(group):
            # If all scorers are NA → return NA
            if group["scorer"].isna().all():
                return np.nan

            # Build strings like: "Birgit Prinz (Germany at 16')"
            parts = (
                group.dropna(subset=["scorer"])
                .apply(lambda r: f"{r.scorer} ({r.team} at {r.minute}')", axis=1)
                .tolist()
            )
            return ", ".join(parts)

        table_data = (
            df.groupby(
                [
                    "date",
                    "tournament",
                    "home_team",
                    "country_flag_home",
                    "home_score",
                    "away_score",
                    "away_team",
                    "country_flag_away",
                ],
                dropna=False,
            )
            .apply(summarize_scorers, include_groups=False)
            .reset_index(name="scorers")
        )

        # Column names + making sure the flag is behind the country name
        display_df = table_data.copy()
        display_df["home_team"] = (
            display_df["home_team"] + " " + display_df["country_flag_home"]
        )
        display_df["away_team"] = (
            display_df["away_team"] + " " + display_df["country_flag_away"]
        )
        display_df = display_df.drop(columns=["country_flag_home", "country_flag_away"])
        display_df = display_df.rename(
            columns={
                "date": "Date",
                "tournament": "Tournament",
                "home_team": "Home Team",
                "home_score": "Home Score",
                "away_score": "Away Score",
                "away_team": "Away Team",
                "scorers": "Scorers",
            }
        )

        # Format date and sort by date descending
        display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
        display_df = display_df.sort_values("Date", ascending=False)

        return render.DataTable(
            display_df,
            styles=[
                # ----- column width rules -----
                {"cols": [0], "style": {"min-width": "100px", "width": "100px"}},
                {"cols": [1], "style": {"min-width": "200px"}},
                {"cols": [2], "style": {"min-width": "150px"}},
                {"cols": [3], "style": {"min-width": "100px"}},
                {"cols": [4], "style": {"min-width": "100px"}},
                {"cols": [5], "style": {"min-width": "150px"}},
                {"cols": [6], "style": {"min-width": "300px", "white-space": "normal"}},
                # ----- striped rows -----
                # even rows
                {
                    "rows": list(range(0, 10_000, 2)),
                    "style": {"background-color": "#e0e1e2"},
                },
            ],
        )


app = App(app_ui, server)
