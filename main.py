"""
This will check Sonarr and Radarr or fake downloads and delete/blacklist accordingly.
Only works on HTTP not HTTPS.
Only works if using HTTP auth (browser popup) login. No security or form login will not work

Q: "Why don't you make it work with https, or other login methods?"
A: "I made this for my setup, if you want to add support for other setups, feel free"
"""

import os
from json import loads
from time import sleep, ctime

import requests
import toml


def main():
    services = SR.load_services()
    while True:
        print("Checking for fakes:", ctime())
        for service in services:
            service.kill_fakes()
        sleep(120)


class SR:  # SR for Sonarr or Radarr
    class Item:
        def __init__(self, item_id, http_pw_url, api_key, usenet, torrent, folder_name, d_type, path):
            self.item_id = item_id
            self.http_pw_url = http_pw_url
            self.api_key = api_key
            self.usenet = usenet  # Completed usenet path
            self.torrent = torrent  # Completed torrents path
            self.folder_name = folder_name
            self.d_type = d_type
            self.path = path if path is not None else self.find_path()

        def find_path(self):
            c_path = self.usenet if self.d_type == "usenet" else self.torrent
            for folder_path, folder_names, file_names in os.walk(c_path):
                for folder_name in folder_names:
                    if folder_name == self.folder_name:
                        return os.path.join(folder_path, folder_name)

        def kill(self):
            requests.delete(
                self.http_pw_url + "/api/queue/{}?blacklist=true&apikey={}".format(self.item_id, self.api_key))
            print("KILLED", self)

        def kill_no_blacklist(self):
            requests.delete(
                self.http_pw_url + "/api/queue/{}?blacklist=false&apikey={}".format(self.item_id, self.api_key))
            print("KILLED", self)

        def __repr__(self):
            return "ID:{} PATH:\"{}\"".format(self.item_id, self.path)

        def __str__(self):
            return "NAME:{} ID:{} PATH:{}".format(self.folder_name, self.item_id, self.path)

    def __init__(self, url, username, password, usenet, torrents):
        self.clear_url = url.replace("http://", "").replace("https://", "").replace("/", "").replace("sonarr", "")
        self.username = username
        self.password = password
        self.http_pw_url = "http://{}:{}@{}".format(self.username, self.password, self.clear_url)  # HTTP auth url
        self.api_key = \
            requests.get(self.http_pw_url, stream=True, timeout=10).text.split("ApiKey     : '")[1].split("'")[0]
        self.usenet = usenet
        self.torrents = torrents

    def kill_fakes(self):
        completed = self.get_completed()
        if len(completed) < 1:
            return
        for download in completed:
            for folder_path, folder_names, file_names in os.walk(download.path):
                for item in folder_names, file_names:
                    for a in item:
                        if ".exe" in a.lower() or "codec" in a.lower() or ".wmv" in a.lower():
                            download.kill()

    def get_completed(self):
        r = requests.get(self.http_pw_url + "/api/queue?apikey=" + self.api_key)
        rdic = loads(r.text)
        items = []
        for x in rdic:
            path = None
            if x['status'] != "Completed" or len(x['statusMessages']) != 1:  # Makes sure only one file
                if len(x['statusMessages'][0]['messages']) != 1:
                    if "Has the same filesize as existing file" in x['statusMessages'][0]['messages']:
                        SR.Item(x['id'], self.http_pw_url, self.api_key, self.usenet, self.torrents, x['title'],
                                x['protocol'], path).kill_no_blacklist()  # Deletes duplicate download
                    else:
                        continue
            if len(x['statusMessages'][0]['messages']) != 1:  # If more than one issue then it may not be fake
                continue
            if "No files found are eligible for import in" in x['statusMessages'][0]['messages'][0]:
                path = x['statusMessages'][0]['messages'][0].replace("No files found are eligible for import in ", "")
            items.append(
                SR.Item(x['id'], self.http_pw_url, self.api_key, self.usenet, self.torrents, x['title'], x['protocol'],
                        path))  # extracts path and id for downloads, and creates Item objects for each
        return items

    @staticmethod
    def load_services():
        services = []
        with open("SR.toml") as configfile:
            for service in toml.loads(configfile.read()).items():
                services.append(
                    SR(service[1]["url"], service[1]["username"], service[1]["password"], service[1]["usenet"],
                       service[1]["torrent"]))
        print("LOADED:")
        for service in services:
            print("    ", service)
        print()
        return services

    def __repr__(self):
        return "URL:\"{}\" USR:\"{}\" PWD:\"{}\"".format(self.clear_url, self.username, self.password)

    def __str__(self):
        return "URL:\"{}\" USR:\"{}\" PWD:\"{}\"".format(self.clear_url, self.username, self.password)


if __name__ == "__main__":
    main()
