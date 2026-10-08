import requests

keys = [
    "AQ.Ab8RN6KL8AYZrPLPqYQd6-qvEKzJIKLxuV3LRMkTEIpmcE4WDg",
    "AIzaSyBLILwSPguZkCTi24q74adZ_4Ep_g88W5Q",
    "AIzaSyBqsJK2tIFi5Uo2ItOr-7uVzycAfV-QT3o"
]

models = [
    "gemini-3.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-pro"
]

for key in keys:
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
        res = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        print(f"Key: {key[:10]}... Model: {model} Status: {res.status_code}")
        if res.status_code == 200:
            print("SUCCESS!")
            break
