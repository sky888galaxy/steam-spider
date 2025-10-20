import requests
requests.packages.urllib3.disable_warnings()  # 屏蔽警告

url = "https://store.steampowered.com"
response = requests.get(url, verify=False)
print(response.status_code)