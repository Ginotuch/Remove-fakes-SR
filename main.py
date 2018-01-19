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
    class Item:
        def __init__(self, path, item_id):
            self.path = path
            self.item_id = item_id

        def __repr__(self):
            return "ID:{} PATH:\"{}\"".format(self.item_id, self.path)

        def __str__(self):
            return "ID:{} PATH:{}".format(self.item_id, self.path)

    def __init__(self, url, username, password):
        self.clear_url = url.replace("http://", "").replace("https://", "").replace("/", "").replace("sonarr", "")
        self.username = username
        self.password = password
        self.http_pw_url = "http://{}:{}@{}".format(self.username, self.password, self.clear_url)
        self.api_key = requests.get(self.http_pw_url, stream=True, timeout=10).text.split("ApiKey     : '")[1].split("'")[0]

    def get_completed(self):
        r = requests.get(self.http_pw_url + "/api/queue?apikey=" + self.api_key)
        rdic = loads(r.text)
        items = []
        for x in rdic:
            if x['status'] != "Completed" or len(x['statusMessages']) != 1:  # Makes sure only one error
                continue
            if len(x['statusMessages'][0]['messages']) != 1:  # If more than one issue may not be fake
                continue
            if "No files found are eligible for import in" not in x['statusMessages'][0]['messages'][0]:
                continue
            items.append(
                SR.Item(x['statusMessages'][0]['messages'][0].replace("No files found are eligible for import in ", ""),
                        x['id']))
        return items
