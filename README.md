# She Scores ⚽️: Women's International Soccer Matches. Available in Python and R.

This repository contains a Shiny for R and Shiny for Python app that is called "SheScores". This dashboard allows users to explore women soccer match results from international competitions.

## About the data

SheScores uses data related to Women's International Football results ⚽️. The data is available in the `data` folder and it contains some pre-processing steps. The data is sourced from [Kaggle](https://www.kaggle.com/datasets/martj42/womens-international-football-results?resource=download).

*Note that an earlier demo version of this app was built during the ShinyConf2024 workshop on building modular Shiny apps (["Shiny 101: Modular App BluePrint"](https://github.com/hypebright/shinyconf2024-shiny101))*

## Read the blog

This app is used in "Where Questions Become Queries: Meet querychat" on the Shiny blog. But you need to have a bit more patience... the blog will be published soon!

This blog post introduces `querychat`, a package that allows users to interact with their Shiny applications using natural language queries. By leveraging LLMs, `querychat` enables users to ask questions about their data in plain English, receive accurate responses, and even automatically update the dashboard views based on their queries. 

The best thing? All of it is **safe**. Yep, you read that right! The model never has access to the raw data, produces read-only queries, and you can log or review every generated query. You are in control. 