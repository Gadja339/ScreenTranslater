import requests

url = "https://api.mymemory.translated.net/get"

params = {
    "q": "window",
    "langpair": "en|ru"
}

response = requests.get(
    url,
    params=params,
    timeout=5
)

response.raise_for_status()

data = response.json()

translation = data["responseData"]["translatedText"]

print(translation)