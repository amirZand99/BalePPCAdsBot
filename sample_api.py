url = "https://randomuser.me/api/"
import requests

result = requests.request("GET", url)
print(result.json())