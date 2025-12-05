# Dataset description
This dataset contains international women’s football match results. It includes match metadata (date, location, teams), outcomes (scores), plus optional event-level information such as individual scorers. Not all friendly matches are represented; major tournaments are mostly complete.

# Column descriptions
- date (string, YYYY-MM-DD): The calendar date on which the match was played.
- home_team (string): Name of the home team.
- date (string, YYYY-MM-DD): The calendar date on which the match was played.
- home_team (string): Name of the home team.
- away_team (string): Name of the away team.
- home_score (integer): Goals scored by the home team at full time (extra time included, - penalty shoot-outs excluded).
- away_score (integer): Goals scored by the away team at full time (extra time included, - penalty shoot-outs excluded).
- tournament (string): Name of the competition or event.
- city (string): City or administrative area where the match was played.
- country (string): Country where the match was played.
- neutral (boolean): Indicates whether the match took place at a neutral venue.
- team (string, optional): Team associated with a recorded scoring event.
- scorer (string, optional): Player who scored the goal.
- minute (integer, optional): Match minute in which the goal occurred.
- own_goal (boolean, optional): Indicates whether the goal was an own goal.
- penalty (boolean, optional): Indicates whether the goal was scored from a penalty kick.
- country_flag_home (string): Emoji or symbol representing the home country.
- country_flag_away (string): Emoji or symbol representing the away country.
- continent (string): Continent associated with the home country.
- country_code (string): Country code associated with the home team (e.g., ISO-like).
- latitude (float): Latitude of the match location.
- longitude (float): Longitude of the match location.
- match_id (string): Unique identifier for the match, typically based on date and team names.