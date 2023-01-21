import requests
import csv
import time
import dateutil.parser as dt
from datetime import datetime
import os

####################
# IMPORTANT: DO NOT SHARE YOUR TOKEN WITH OTHERS
####################
start_date = "1970-12-31"
end_date = datetime.now().strftime("%Y-%m-%d") #Today
sport = "TENNIS"

#####################
# Do not edit below this line!
#####################
class WinnerOddsExporter:
    def __init__(self, start_date, end_date, sport):
        self.start_date = start_date
        self.end_date = end_date
        self.sport = sport
        self.csv_path = f"winnerodds_bets_{sport}_{start_date}_{end_date}.csv"
        self.api_url = "https://app.winnerodds.com:4000/graphql"
        self.last_print = ""

        if not os.path.exists("token.txt"):
            raise FileExistsError("token.txt does not exist")
        
        with open("token.txt") as f:
            self.token = f.read()

    def run(self):
        has_more = True
        page_num = -1

        self.print('Loading bookies')
        bookies = self.GetBookies()

        self.print(f'Creating {self.csv_path}')
        f = open(self.csv_path, 'w', encoding='UTF8', newline='')
        csv_writer = csv.writer(f)

        try:
            while (has_more):
                page_num += 1
                self.print(f'Processing page {page_num}')

                has_more = self.GetBets(page_num, bookies, csv_writer)

                time.sleep(1) # Sleep so we don't flood the server with requests
        finally:
            f.close()
            self.print("Done")


    def print(self, message):
        self.last_print = message
        print(message)


    def ApiRequest(self, query):
        r = requests.post(self.api_url, json=query, headers={
            'Origin': 'https://app.winnerodds.com',
            'authorization': 'Bearer ' + self.token,
        })

        if r.status_code == 500:
            raise Exception(f"Status code {r.status_code}: {r.reason}. Check if your token is correct.")
        if r.status_code != 200:
            raise Exception(f"Status code {r.status_code}: {r.reason}")

        return r.json()


    def GetBookies(self):
        data = self.ApiRequest(self.QueryBookies())

        bookies = {}
        for b in data['data']['getBookies']:
            bookies[b['id']] = b['name']

        return bookies


    def GetBets(self, page_num, bookies, csv_writer):
        data = self.ApiRequest(self.QueryBetHistory(page_num))

        has_more = data['data']['getStatsMatches']['hasMore']
        matches = data['data']['getStatsMatches']['matches']

        if (page_num == 0):
            csv_writer.writerow([
                'bet_at',
                'match_date',
                'sportsbook',
                'sport',
                'tournament',
                'team1',
                'team2',
                'rule',
                'line',
                'odds',
                'stake_money',
                'stake_units',
                'profit',
                'status',
                'match_result',
            ])
        
        for match in matches:
            csv_writer.writerow([
                dt.parse(match['betAt']).strftime("%Y-%m-%d %H:%M:%S"),
                dt.parse(match['matchDate']).strftime("%Y-%m-%d %H:%M:%S"),
                bookies[match['bookieId']],
                self.sport,
                match['tournamentName'],
                match['team1'],
                match['team2'],
                match['rule'],
                match['line'],
                match['quota'],
                f"{match['amount']:0.2f}",
                f"{match['units']:0.2f}",
                f"{match['benefitMoney']:0.2f}",
                match['status'],
                match['matchResult']
            ])
        
        return has_more


    def QueryBetHistory(self, page_num):
        query = {
            "operationName":"getStatsMatches",
            "variables":{
                "statsFilter":{
                    "period":None,
                    "tournament":None,
                    "color":None,
                    "live":None,
                    "bookie":"",
                    "search":"",
                    "period":[
                        self.start_date,
                        self.end_date
                    ]
                },
                "statsPagination":{"my_page":page_num,"per_page":50},
                "sport": self.sport
            },
            "query":"""query getStatsMatches($sport: String, $matches: Boolean, $statsFilter: StatsFilter, $statsPagination: StatsPagination)
        {
            getStatsMatches(
            sport: $sport
            matches: $matches
            statsFilter: $statsFilter
            statsPagination: $statsPagination
            ) {
                matches {
                    id
                    matchId
                    line
                    status
                    benefitMoney
                    bookieId
                    quota
                    amount
                    units
                    betAt
                    rule
                    matchDate
                    matchResult
                    color
                    team1
                    team2
                    tournamentName
                    country
                    matchWinner
                    }
                hasMore
            }
        }"""}

        return query


    def QueryBookies(self):
        return {
            "operationName":"getBookies",
            "variables":{
                "sport": self.sport
            },
            "query":"""
    query getBookies($sport: Sport)
    { 
        getBookies(sport: $sport) {
            ...BookieFragment
        }
    }

    fragment BookieFragment on Bookie
    {
        id
        name
        slug
        nicename
    }
    """}


if __name__ == "__main__":
    exporter = WinnerOddsExporter(start_date, end_date, sport)
    exporter.run()