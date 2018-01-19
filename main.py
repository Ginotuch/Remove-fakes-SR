"""
This will check Sonarr and Radarr or fake downloads and delete/blacklist accordingly.
Only works on HTTP not HTTPS.
Only works if using HTTPauth (browser popup) login. No security or form login will not work

Q: "Why don't you make it work with https, or other login methods?"
A: "I made this for my setup, if you want to add support for other setups, feel free"
"""

from json import loads
import requests


def main():
    pass


class SR:  # SR for Sonarr or Radarr
    def __init__(self, url, username, password):
        self.clear_url = url.replace("http://", "").replace("https://", "").replace("/", "").replace("sonarr", "")
        self.username = username
        self.password = password
        self.http_pw_url = "http://{}:{}@{}".format(self.username, self.password, self.clear_url)
        self.api_key = requests.get(self.http_pw_url, stream=True, timeout=10).text.split("ApiKey     : '")[1].split("'")[0]

    def get_completed(self):
        r = requests.get("http://{}:{}@")
