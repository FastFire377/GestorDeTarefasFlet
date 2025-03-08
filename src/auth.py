from flask import Flask, request, redirect
import os
import requests

CLIENT_ID = "Ov23liC7fvBOl99Nbrab"
CLIENT_SECRET = "b0f46f2b54b999f9e7e4e888bce1cce30f3d5ada"

app = Flask(__name__)

@app.route("/")
def home():
    return '<a href="https://github.com/login/oauth/authorize?client_id=' + CLIENT_ID + '">Login with GitHub</a>'

@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_url = "https://github.com/login/oauth/access_token"
    data = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "code": code}
    headers = {"Accept": "application/json"}
    response = requests.post(token_url, data=data, headers=headers)
    token = response.json().get("access_token")

    if token:
        user_data = requests.get("https://api.github.com/user", headers={"Authorization": f"token {token}"})
        user_info = user_data.json()
        return f"✅ Welcome, {user_info['login']}!"

    return "⚠️ Authentication failed."

app.run(host="0.0.0.0", port=8080)
