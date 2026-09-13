import requests


def fetch_mutual_fund_data(scheme_code):
  url = f'https://api.mfapi.in/mf/{scheme_code}'
  response = requests.get(url)
  if response.status_code == 200:
    data = response.json()
    return data
  return None