#!/usr/bin/python

import json
import requests
import pandas as pd

SPORTSBOOKS = {
    "BetMGM": "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?bookmakers=betmgm&apiKey=YOUR_API_KEY",
    "DraftKings": "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?bookmakers=draftkings&apiKey=YOUR_API_KEY",
    "FanDuel": "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?bookmakers=fanduel&apiKey=YOUR_API_KEY",
    "PointsBet": "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?bookmakers=pointsbetus&apiKey=YOUR_API_KEY",
    "Caesars": "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?bookmakers=caesars&apiKey=YOUR_API_KEY"
}

TEST_ODDS_FILE       = 'sample_odds.json'
TEST_HISTORICAL_FILE = 'historical_mlb_trends.csv'

# Only bet on teams with a cover rate above this
MIN_COVER_RATE = 52


###############################################################################
#
# Procedure   : GetOdds()
#
# Description : Load test MLB odds data from sample_odds_json ...
#               - Simulates real-time sportsbook odds for testing.
#               - Each game includes multiple bookmakers and respective 
#                  moneylines.
#
# Input       : -none- 
#
# Returns     : List of dictionaries with game odds in this format ... 
#                   [
#                       {
#                           "game": "<Team A> vs <Team B>",
#                           "odds": {
#                             "DraftKings": {"Team A": -130, "Team B": 110},
#                             "FanDuel": {"Team A": -128, "Team B": 108},
#                             ...
#                           }
#                       },
#                       ...
#                   ]
#               If error occurs loading file ... returns empty list [].
#
###############################################################################

def GetOdds():

    try:
        with open("sample_odds.json", "r") as file:

            allOdds = json.load(file)
            print("✅ Loaded test odds data from sample_odds.json.")
            return allOdds

    except Exception as e:

        print(f"❌ Error loading odds data: {e}")
        return [] 

    return allOdds


###############################################################################
#
# Procedure   : LoadHistoricalData()
#
# Description : Loads historical MLB team trends via historical_mlb_trends.csv 
#               - File contains past performance data.
#               - Each teams overage cover rate percentage.
#
# Input       : -none-
#
# Returns     : Pandas DataFrame with columns:
#               - team        : Team name (string)
#               - cover_rate  : Historical cover rate as a percentage (float)
#
#               Example:
#               - team,cover_rate
#                   Yankees,54.2
#                   Red Sox,51.8
#
#               If file fails to load, returns empty DataFrame.
#
###############################################################################

def LoadHistoricalData():

    try:
        data = pd.read_csv(TEST_HISTORICAL_FILE)
        print("✅ Loaded historical MLB trends from historical_mlb_trends.csv.")
        return data

    except Exception as e:
        print(f"❌ Error loading historical data: {e}")
        return pd.DataFrame()


###############################################################################
#
# Procedure   : FindBestBets()
#
# Description : Analyze loaded MLB odds and historical data to identify the 
#               top 5 best bets of the day, we do this by ... 
#
#               - Loop through each game in the odds dataset.
#               - For each game, loop through all available sportsbooks to 
#                 find most favorable moneyline for each team.
#               - Cross-references each team against historical performance 
#                 data to retrieve their average cover rate percentage.
#               - Adds both teams from each game into the best bets pool, 
#                 including ...
#                 * Best available moneyline across all books.
#                 * Historical cover rate.
#                 * Full list of odds from all books for display.
#               - Sorts the pool by highest cover rate to rank the strongest edges.
#               - Returns the top 5 bets based on cover rate.
#
# Input       : -none- 
#
# Returns     : List of up to 5 dictionaries, each representing a best bet:
#                   [
#                     {
#                       "game": "<Team A> vs <Team B>",
#                       "team": "<Team A>",
#                       "moneyline": <best available moneyline>,
#                       "cover_rate": <historical cover rate>,
#                       "odds": {
#                           "DraftKings": {...},
#                           "FanDuel": {...},
#                           ...
#                        }
#                     },
#                     ...
#                   ]
#
###############################################################################

def FindBestBets():

    odds = GetOdds()
    historicalData = LoadHistoricalData()

    bestBets = []
    usedTeams = set()

    for game in odds:

        gameName = game["game"]
        allBookmakers = game["odds"]

        # Grab the team names from the first bookmaker
        firstBookmaker = next(iter(allBookmakers.values()))
        team1, team2 = list(firstBookmaker.keys())

        # Find the best odds across all books
        bestOdds1 = max(moneylines[team1] for moneylines in allBookmakers.values())
        bestOdds2 = max(moneylines[team2] for moneylines in allBookmakers.values())

        # Find cover rates
        team1History = historicalData[historicalData["team"] == team1]
        team2History = historicalData[historicalData["team"] == team2]

        coverRate1 = team1History["cover_rate"].values[0] if not team1History.empty else 50
        coverRate2 = team2History["cover_rate"].values[0] if not team2History.empty else 50

        # Add team 1 if it qualifies
        if team1 not in usedTeams and coverRate1 >= MIN_COVER_RATE:
            bestBets.append({
                "game": gameName,
                "team": team1,
                "moneyline": bestOdds1,
                "cover_rate": coverRate1,
                "odds": allBookmakers
            })
            usedTeams.add(team1)

        # Add team 2 if it qualifies
        if team2 not in usedTeams and coverRate2 >= MIN_COVER_RATE:
            bestBets.append({
                "game": gameName,
                "team": team2,
                "moneyline": bestOdds2,
                "cover_rate": coverRate2,
                "odds": allBookmakers
            })
            usedTeams.add(team2)

        # Stop if we hit 5 bets
        if len(bestBets) >= 5:
            break

    # Sort by cover rate, just in case
    bestBets = sorted(bestBets, key=lambda x: x["cover_rate"], reverse=True)

    return bestBets


###############################################################################
#
# Procedure   : Main
#
# Description : Entry point.
#
# Input       : -none-
#
# Returns     : -none-
#
###############################################################################

def Main():

    print("📊 Fetching MLB betting data...")

    bestBets = FindBestBets()

    if bestBets:

        print("\n🔥 Today's Best Bets:")

        for bet in bestBets:

            print(f"Game: {bet['game']} - Team: {bet['team']} - Moneyline: {bet['moneyline']} - Cover Rate: {bet['cover_rate']}%")

            for bookmaker, lines in bet['odds'].items():
                print(f"  {bookmaker}: {lines}")

    else:
        print("❌ No best bets available today.")


if __name__ == "__main__":
    Main()

