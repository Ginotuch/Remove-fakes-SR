"""
This will check Sonarr and Radarr or fake downloads and delete/blacklist accordingly.
Only works on HTTP not HTTPS.
Only works if using HTTP auth (browser popup) login. No security or form login will not work

Q: "Why don't you make it work with https, or other login methods?"
A: "I made this for my setup, if you want to add support for other setups, feel free"
"""

import os
from json import loads
from time import sleep

import requests
import toml


def main():
    services = SR.load_services()
    while True:
        for service in services:
            service.kill_fakes()
        sleep(120)


class SR:  # SR for Sonarr or Radarr
    class Item:
        def __init__(self, path, item_id, http_pw_url, api_key):
            self.path = path
            self.item_id = item_id
            self.http_pw_url = http_pw_url
            self.api_key = api_key

        def kill(self):
            requests.delete(self.http_pw_url + "/api/queue/{}?blacklist=true&apikey={}".format(self.item_id, self.api_key))

        def __repr__(self):
            return "ID:{} PATH:\"{}\"".format(self.item_id, self.path)

        def __str__(self):
            return "ID:{} PATH:{}".format(self.item_id, self.path)

    def __init__(self, url, username, password):
        self.clear_url = url.replace("http://", "").replace("https://", "").replace("/", "").replace("sonarr", "")
        self.username = username
        self.password = password
        self.http_pw_url = "http://{}:{}@{}".format(self.username, self.password, self.clear_url)  # HTTP auth url
        self.api_key = \
        requests.get(self.http_pw_url, stream=True, timeout=10).text.split("ApiKey     : '")[1].split("'")[0]

    def kill_fakes(self):
        completed = self.get_completed()
        if len(completed) < 1:
            return
        for download in completed:
            f_dir = os.listdir(download.path)
            if "codec" in [x.lower() for x in f_dir]:
                download.kill()
            if True in [".exe" in x.lower() for x in f_dir]:
                download.kill()

    def get_completed(self):
        r = requests.get(self.http_pw_url + "/api/queue?apikey=" + self.api_key)
        rdic = loads(r.text)
        items = []
        for x in rdic:
            if x['status'] != "Completed" or len(x['statusMessages']) != 1:  # Makes sure only one file
                continue
            if len(x['statusMessages'][0]['messages']) != 1:  # If more than one issue then it may not be fake
                continue
            if "No files found are eligible for import in" not in x['statusMessages'][0]['messages'][0]:
                continue
            items.append(
                SR.Item(x['statusMessages'][0]['messages'][0].replace("No files found are eligible for import in ", ""),
                        x['id'], self.http_pw_url, self.api_key))  # extracts path and id for downloads, and creates Item objects for each
        return items

    @staticmethod
    def load_services():
        services = []
        with open("SR.toml") as configfile:
            for service in toml.loads(configfile.read()).items():
                services.append(SR(service[1]["url"], service[1]["username"], service[1]["password"]))
        return services

    def __repr__(self):
        return "URL:\"{}\" USR:\"{}\" PWD:\"{}\"".format(self.clear_url, self.username, self.password)


if __name__ == "__main__":
    main()
