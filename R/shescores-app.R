# global ------------------------------------------------
library(shiny)
library(bslib)
library(shinyWidgets)
library(lubridate)
library(dplyr)
library(echarts4r)
library(leaflet)
library(tidyr)
library(reactable)

# ===============================
# Setup
# ===============================
# read in data
# note that for demo purposes this is in a top-level folder
# normally, you would have this inside the folder that contains app.R
results_with_scorers <- read.csv("../data/results_with_scorers.csv") |>
  filter(tournament != "Friendly", date >= "2000-01-01")

soccer_icon <- makeIcon(
  iconUrl = "https://openmoji.org/data/color/svg/26BD.svg",
  iconWidth = 25,
  iconHeight = 25
)

# ===============================
# UI
# ===============================
ui <- page_sidebar(
  fillable = FALSE,
  title = "She Scores ⚽️: Women's International Soccer Matches",
  sidebar = sidebar(
    title = "Filters",
    width = "30%",
    # Year filter
    sliderInput(
      inputId = "year_filter",
      label = "Select year range:",
      min = year(min(as.Date(results_with_scorers$date))),
      max = year(max(as.Date(results_with_scorers$date))),
      value = c(
        year(min(as.Date(results_with_scorers$date))),
        year(max(as.Date(results_with_scorers$date)))
      ),
      sep = ""
    ),
    # Continent filter (dropdown)
    pickerInput(
      inputId = "continent_filter",
      label = "Select continents:",
      choices = sort(unique(results_with_scorers$continent)),
      selected = sort(unique(results_with_scorers$continent)),
      options = pickerOptions(
        actionsBox = TRUE,
        selectedTextFormat = "count > 1",
        countSelectedText = "{0} continents selected"
      ),
      multiple = TRUE
    ),
    # Tournament filter (dropdown)
    pickerInput(
      inputId = "tournament_filter",
      label = "Select tournaments:",
      choices = NULL,
      selected = NULL,
      options = pickerOptions(
        actionsBox = TRUE,
        liveSearch = TRUE,
        liveSearchPlaceholder = "Search for a tournament",
        selectedTextFormat = "count > 1",
        countSelectedText = "{0} tournaments selected"
      ),
      multiple = TRUE
    ),
    # Switch to show data with scorers only
    input_switch(
      id = "scorer_only",
      label = "Show matches with scorer data only",
      value = FALSE
    ),
  ),
  layout_columns(
    value_box(
      title = "Top scoring country",
      value = textOutput("top_country")
    ),
    value_box(
      title = "Top scorer",
      value = textOutput("top_scorer"),
      textOutput("top_scorer_missing")
    ),
    value_box(
      title = "Total countries",
      value = textOutput("total_countries")
    )
  ),
  layout_columns(
    # Map with tournament locations
    card(
      leafletOutput("map"),
      min_height = "500px"
    ),
    card(
      echarts4rOutput("overview"),
      min_height = "500px"
    )
  ),
  layout_columns(
    card(
      title = "Match Results",
      reactableOutput("results_table"),
      min_height = "700px"
    )
  )
)

# ===============================
# Server
# ===============================
server <- function(input, output, session) {
  # Reactive filtered data based on inputs
  filtered_data <- reactive({
    req(length(input$continent_filter) > 0)
    req(length(input$tournament_filter) > 0)

    results_with_scorers |>
      mutate(date = as.Date(date)) |>
      filter(
        year(date) >= input$year_filter[1],
        year(date) <= input$year_filter[2],
        continent %in% input$continent_filter,
        tournament %in% input$tournament_filter,
        if (input$scorer_only) {
          !is.na(scorer)
        } else {
          TRUE
        }
      )
  })

  # Debounce filtered_data to avoid excessive reactivity
  filtered_data_debounced <- filtered_data |> debounce(500)

  output$top_country <- renderText({
    # get the top scoring country in the filtered data (both home_team and away_team)
    top_country <- filtered_data_debounced() |>
      group_by(date, home_team, tournament) |>
      summarise(
        country = first(home_team),
        # count of unique tournaments played
        matches = length(unique(tournament)),
        goals = first(home_score),
        country_flag = first(country_flag_home),
        .groups = "drop"
      ) |>
      bind_rows(
        filtered_data_debounced() |>
          group_by(date, away_team, tournament) |>
          summarise(
            country = first(away_team),
            matches = length(unique(tournament)),
            goals = first(away_score),
            country_flag = first(country_flag_away),
            .groups = "drop"
          )
      ) |>
      group_by(country) |>
      summarise(
        matches = sum(matches),
        goals = sum(goals),
        country_flag = first(country_flag),
        .groups = "drop"
      ) |>
      arrange(desc(goals)) |>
      slice(1)

    paste0(
      top_country$country,
      "",
      top_country$country_flag
    )
  })

  output$top_scorer_missing <- renderText({
    missing_scorer_pct <- filtered_data_debounced() |>
      summarise(
        missing = sum(is.na(scorer)),
        total = n(),
        pct = missing / total * 100
      ) |>
      pull(pct)

    paste0(
      "Missing scorer data: ",
      round(missing_scorer_pct, 2),
      "%"
    )
  })

  output$top_scorer <- renderText({
    # get the top scorer in the filtered data
    top_scorer <- filtered_data_debounced() |>
      # remove NAs in scorer
      filter(!is.na(scorer)) |>
      # get country flag for team
      mutate(
        country_flag = ifelse(
          team == home_team,
          country_flag_home,
          country_flag_away
        )
      ) |>
      group_by(scorer, country_flag) |>
      summarise(
        goals = n(),
        .groups = "drop"
      ) |>
      arrange(desc(goals)) |>
      # get top scorer with highest number of goals
      slice(1)

    paste0(
      top_scorer$scorer,
      " ",
      top_scorer$country_flag
    )
  })

  output$total_countries <- renderText({
    # get the total number of unique countries in the filtered data
    total_countries <- filtered_data_debounced() |>
      select(home_team, away_team) |>
      pivot_longer(
        cols = everything(),
        names_to = "team_type",
        values_to = "country"
      ) |>
      distinct(country) |>
      nrow()

    total_countries
  })

  output$overview <- renderEcharts4r({
    # get the number of matches over time
    filtered_data_debounced() |>
      group_by(date = lubridate::floor_date(date, "year")) |>
      summarise(matches = length(unique(match_id)), .groups = "drop") |>
      e_charts(date) |>
      e_line(
        matches,
        lineStyle = list(
          width = 3,
          color = "#0f0437"
        )
      ) |>
      e_title(
        "Matches over time",
        textStyle = list(
          fontSize = 26
        )
      ) |>
      e_tooltip() |>
      e_legend(show = FALSE)
  })

  output$map <- renderLeaflet({
    # get unique tournament locations
    locations <- filtered_data_debounced() |>
      # remove rows with missing lat/lon
      filter(!is.na(latitude), !is.na(longitude)) |>
      select(tournament, latitude, longitude, city, date) |>
      # add year for popup and condense information (comma separated years for same tournament)
      mutate(year = year(as.Date(date))) |>
      group_by(tournament, latitude, longitude, city) |>
      summarise(
        years = paste(sort(unique(year)), collapse = ", "),
        .groups = "drop"
      ) |>
      distinct()

    # if no locations, create empty map
    if (nrow(locations) == 0) {
      return(
        leaflet() |>
          addProviderTiles(providers$CartoDB.Positron)
      )
    } else {
      leaflet(data = locations) |>
        addProviderTiles(providers$CartoDB.Positron) |>
        # group markers to improve performance
        addMarkers(
          ~longitude,
          ~latitude,
          icon = soccer_icon,
          # in popup, show tournament name, year, and results (table format)
          popup = ~ paste0(
            "<strong>",
            tournament,
            "</strong>",
            "<br/>",
            "Location: ",
            city,
            "<br/>",
            "Years held: ",
            years
          ),
          clusterOptions = markerClusterOptions(
            spiderfyOnMaxZoom = TRUE,
            showCoverageOnHover = TRUE,
            zoomToBoundsOnClick = TRUE
          )
        )
    }
  })

  output$results_table <- renderReactable({
    # Collapse scorers into a single string per match
    table_data <- filtered_data_debounced() |>
      group_by(
        date,
        tournament,
        home_team,
        country_flag_home,
        home_score,
        away_score,
        away_team,
        country_flag_away
      ) |>
      summarise(
        # e.g. Birgit Prinz (Germany at 16'), Sara Johansson (England at 45')
        # if no data, return NA
        scorers = if (all(is.na(scorer))) {
          NA
        } else {
          paste0(
            na.omit(
              paste0(scorer, " (", team, " at ", minute, "')")
            ),
            collapse = ", "
          )
        },
        .groups = "drop"
      )

    reactable(
      table_data,
      columns = list(
        date = colDef(
          name = "Date",
          format = colFormat(date = TRUE),
          minWidth = 100
        ),
        tournament = colDef(name = "Tournament", minWidth = 150),
        home_team = colDef(
          name = "Home Team",
          cell = function(value, index) {
            flag <- table_data$country_flag_home[index]
            htmltools::HTML(paste0(flag, " ", value))
          },
          minWidth = 150
        ),
        home_score = colDef(name = "Home Score", minWidth = 110),
        away_score = colDef(name = "Away Score", minWidth = 110),
        away_team = colDef(
          name = "Away Team",
          cell = function(value, index) {
            flag <- table_data$country_flag_away[index]
            htmltools::HTML(paste0(flag, " ", value))
          },
          minWidth = 150
        ),
        scorers = colDef(name = "Scorers", minWidth = 300),
        country_flag_home = colDef(show = FALSE),
        country_flag_away = colDef(show = FALSE)
      ),
      defaultSorted = "date",
      defaultSortOrder = "desc",
      defaultPageSize = 10,
      searchable = TRUE,
      filterable = FALSE,
      highlight = TRUE,
      bordered = TRUE,
      striped = TRUE,
      compact = TRUE
    )
  })

  # Filter down tournaments based on continent
  observe({
    req(input$continent_filter)

    updated_tournaments <- results_with_scorers |>
      filter(continent %in% input$continent_filter) |>
      distinct(tournament) |>
      arrange(tournament) |>
      pull(tournament)

    updatePickerInput(
      session,
      inputId = "tournament_filter",
      choices = sort(updated_tournaments),
      selected = sort(updated_tournaments)
    )
  })
}

shinyApp(ui, server)
