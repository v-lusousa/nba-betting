from bs4 import BeautifulSoup
import pandas as pd
import requests

# Database to fix teams with 2 word names get split
name_changer = {
    'State': 'Golden State',
    'Warriors': 'Golden State',
    'Clippers': 'LA Clippers',
    'Lakers': 'LA Lakers',
    'Orleans': 'New Orleans',
    'Pelicans': 'New Orleans',
    'York': 'New York',
    'Knicks': 'New York',
    'City': 'Okla City',
    'Thunder': 'Okla City',
    'Antonio': 'San Antonio',
    'Spurs': 'San Antonio',
    'Blazers': 'Portland'
}

# Empty pandas table creation
my_columns = ['Team', 'Win %','MOV', 'MOV Last 3', 'ATS +/-', 'Cover %', 'Over %', 'Total +/-', 'PPG 2020', 'PPG Last 3']
teams = pd.DataFrame(columns = my_columns)

## Pull raw code from 4 different pages, parse data, and populate table.

data = requests.get('https://www.teamrankings.com/nba/trends/win_trends/')
soup = BeautifulSoup(data.text, 'html.parser')
for team in soup.find_all('tr'):
    team = team.text.split()
    if len(team) == 8:
        continue
    if len(team) == 6:
        team[1] = name_changer[team[1]]
        del team[0]
    teams = teams.append(
                        pd.Series([team[0], 
                                    float(team[2].strip('%')), 
                                    float(team[3]),
                                    'N/A',
                                    float(team[4]),
                                    'N/A',
                                    'N/A',
                                    'N/A',
                                    'N/A',
                                    'N/A'], 
                                    index = my_columns), 
                        ignore_index = True)


data = requests.get('https://www.teamrankings.com/nba/trends/ats_trends/')
soup = BeautifulSoup(data.text, 'html.parser')
for team in soup.find_all('tr'):
    team = team.text.split()
    if len(team) == 8:
        continue
    if len(team) == 6:
        team[1] = name_changer[team[1]]
        del team[0]
    teams.loc[teams['Team'] == team[0], 'Cover %'] = float(team[2].strip('%'))


data = requests.get('https://www.teamrankings.com/nba/trends/ou_trends/')
soup = BeautifulSoup(data.text, 'html.parser')
for team in soup.find_all('tr'):
    team = team.text.split()
    if len(team) == 9:
        continue
    if len(team) == 6:
        team[1] = name_changer[team[1]]
        del team[0]
    teams.loc[teams['Team'] == team[0], 'Over %'] = float(team[2].strip('%'))
    teams.loc[teams['Team'] == team[0], 'Total +/-'] = float(team[4])


data = requests.get('https://www.teamrankings.com/nba/stat/points-per-game')
soup = BeautifulSoup(data.text, 'html.parser')
for team in soup.find_all('tr'):
    team = team.text.split()
    if len(team) == 10:
        continue
    if len(team) == 9:
        team[2] = name_changer[team[2]]
        del team[1]
    teams.loc[teams['Team'] == team[1], 'PPG 2020'] = float(team[2])
    teams.loc[teams['Team'] == team[1], 'PPG Last 3'] = float(team[3])


data = requests.get('https://www.teamrankings.com/nba/stat/average-scoring-margin')
soup = BeautifulSoup(data.text, 'html.parser')
for team in soup.find_all('tr'):
    team = team.text.split()
    if len(team) == 10:
        continue
    if len(team) == 9:
        team[2] = name_changer[team[2]]
        del team[1]
    teams.loc[teams['Team'] == team[1], 'MOV Last 3'] = float(team[3])


## Create over/under table

matchup_totals_columns = ['Away', 'Home', 'Total O/U', 'Comb. PPG 2020', 'Comb. PPG Last 3', 'Comb. TPG 2020', 'Comb. TPG Last 3', 'Comb. Total +/- Avg', 'Over % Avg']
matchup_totals = pd.DataFrame(columns = matchup_totals_columns)

# API from https://the-odds-api.com/liveapi/guides/v3/
api_par = {'apiKey': 'fa5793b6757a17fdc7222f661b6b0d88',
            'dateFormat': 'iso',
            'sport': 'basketball_nba',
            'region': 'us',
            'mkt': 'totals'}

api_call = f"https://api.the-odds-api.com/v3/odds/?apiKey={api_par['apiKey']}&dateFormat={api_par['dateFormat']}&sport={api_par['sport']}&region={api_par['region']}&mkt={api_par['mkt']}"
data = requests.get(api_call)
for game in data.json()['data']:
    if len(game['teams'][0].split(' ')) > 2:
        away = name_changer[game['teams'][0].split(' ')[2]]
    else:
        away = game['teams'][0].split(' ')[0]
    if len(game['teams'][1].split(' ')) > 2:
        home = name_changer[game['teams'][1].split(' ')[2]]
    else:
        home = game['teams'][1].split(' ')[0]
    for site in game['sites']:
        if site['site_key'] == 'fanduel':
            total_ou = float(site['odds']['totals']['points'][0])

    matchup_totals = matchup_totals.append(
                            pd.Series([away,
                                        home,
                                        total_ou,
                                        (teams.loc[teams['Team'] == away, 'PPG 2020'].values[0] + teams.loc[teams['Team'] == home, 'PPG 2020'].values[0]),
                                        (teams.loc[teams['Team'] == away, 'PPG Last 3'].values[0] + teams.loc[teams['Team'] == home, 'PPG Last 3'].values[0]),
                                        (((teams.loc[teams['Team'] == away, 'PPG 2020'].values[0] * 2) - teams.loc[teams['Team'] == away, 'MOV'].values[0])\
                                         + ((teams.loc[teams['Team'] == home, 'PPG 2020'].values[0] * 2) - teams.loc[teams['Team'] == home, 'MOV'].values[0])) / 2,
                                         (((teams.loc[teams['Team'] == away, 'PPG Last 3'].values[0] * 2) - teams.loc[teams['Team'] == away, 'MOV Last 3'].values[0])\
                                         + ((teams.loc[teams['Team'] == home, 'PPG Last 3'].values[0] * 2) - teams.loc[teams['Team'] == home, 'MOV Last 3'].values[0])) / 2,
                                        (teams.loc[teams['Team'] == away, 'Total +/-'].values[0] + teams.loc[teams['Team'] == home, 'Total +/-'].values[0]) / 2,
                                        (teams.loc[teams['Team'] == away, 'Over %'].values[0] + teams.loc[teams['Team'] == home, 'Over %'].values[0]) / 2],
                                        index = matchup_totals_columns), 
                            ignore_index = True)


## Create spreads table

matchup_spreads_columns = ['Team', 'Spread', 'ATS +/- Avg', 'MOV', 'MOV3', 'Cover %', 'Win %']
matchup_spreads = pd.DataFrame(columns = matchup_spreads_columns)

# API from https://the-odds-api.com/liveapi/guides/v3/
api_par['mkt'] = 'spreads'
api_call = f"https://api.the-odds-api.com/v3/odds/?apiKey={api_par['apiKey']}&dateFormat={api_par['dateFormat']}&sport={api_par['sport']}&region={api_par['region']}&mkt={api_par['mkt']}"
data = requests.get(api_call)
for game in data.json()['data']:
    if len(game['teams'][0].split(' ')) > 2:
        away = name_changer[game['teams'][0].split(' ')[2]]
    else:
        away = game['teams'][0].split(' ')[0]
    if len(game['teams'][1].split(' ')) > 2:
        home = name_changer[game['teams'][1].split(' ')[2]]
    else:
        home = game['teams'][1].split(' ')[0]
    for site in game['sites']:
        if site['site_key'] == 'fanduel':
            away_spread = float(site['odds']['spreads']['points'][0])
            home_spread = float(site['odds']['spreads']['points'][1])
            
            
    matchup_spreads = matchup_spreads.append(
                            pd.Series(['---',
                                        '---',
                                        '---',
                                        '---',
                                        '---',
                                        '---',
                                        '---'],
                                        index = matchup_spreads_columns), 
                            ignore_index = True)

    matchup_spreads = matchup_spreads.append(
                            pd.Series([away,
                                        away_spread,
                                        teams.loc[teams['Team'] == away, 'ATS +/-'].values[0],
                                        teams.loc[teams['Team'] == away, 'MOV'].values[0],
                                        teams.loc[teams['Team'] == away, 'MOV Last 3'].values[0],
                                        teams.loc[teams['Team'] == away, 'Cover %'].values[0],
                                        teams.loc[teams['Team'] == away, 'Win %'].values[0]],
                                        index = matchup_spreads_columns), 
                            ignore_index = True)
    matchup_spreads = matchup_spreads.append(
                            pd.Series([home,
                                        home_spread,
                                        teams.loc[teams['Team'] == home, 'ATS +/-'].values[0],
                                        teams.loc[teams['Team'] == home, 'MOV'].values[0],
                                        teams.loc[teams['Team'] == home, 'MOV Last 3'].values[0],
                                        teams.loc[teams['Team'] == home, 'Cover %'].values[0],
                                        teams.loc[teams['Team'] == home, 'Win %'].values[0]],
                                        index = matchup_spreads_columns), 
                            ignore_index = True)

print()
print(matchup_spreads.to_string(index=False))
print()
print(matchup_totals.to_string(index=False))