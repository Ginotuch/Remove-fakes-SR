import os
import traceback
from json import loads
from time import sleep, ctime

import requests
import toml

from downloaditem import DownloadItem


class SR:  # SR for Sonarr or Radarr
    def __init__(self, url, username, password, usenet, torrents):
        self.clear_url = url.replace("http://", "").replace("https://", "").replace("/", "").replace("sonarr", "")
        self.username = username
        self.password = password
        self.http_pw_url = "http://{}:{}@{}".format(self.username, self.password, self.clear_url)  # HTTP auth url
        self.api_key = \
            requests.get(self.http_pw_url, stream=True, timeout=10).text.split("ApiKey     : '")[1].split("'")[0]
        self.usenet = usenet
        self.torrents = torrents
        self.current_work = ""

    def kill_fakes(self) -> None:
        completed: list = self.get_bad_downloads()
        if len(completed) > 0:
            if len(completed) < 1:
                return
            for download in completed:
                if download.path is None:
                    continue
                bad = False
                for folder_path, folder_names, file_names in os.walk(download.path):
                    for item in folder_names, file_names:
                        for a in item:
                            if ".exe" in a.lower() or "codec" in a.lower() or ".wmv" in a.lower():
                                bad = True
                if bad:
                    download.kill()
                    SR.logging("KILLED: {}".format(str(download)), False)

    def get_bad_downloads(self) -> list:  # To then delete/discard, is only called by kill_fakes()
        downloads = []
        try:
            r = requests.get(self.http_pw_url + "/api/queue?apikey=" + self.api_key)
        except:
            text = "An error occurred on {} from {} in the get_bad_downloads() function (first request):\n{}\n\n\
            Title of error: {}"
            SR.logging(
                text.format(ctime(), self.clear_url, str(traceback.format_exc()), self.current_work), True)
        else:
            rdic = loads(r.text)  # rdic is a dictionary loaded json of all current downloads from Sonarr or Radarr
            for x in rdic:  # Will append bad downloads to the "downloads" list
                self.current_work = x["title"]
                path = None
                try:
                    if "status" in x:
                        if x["status"] in ("Delay", "Pending", "DownloadClientUnavailable"):
                            continue
                    if len(x['statusMessages']) == 1:
                        if "Has the same filesize as existing file" in x['statusMessages'][0]['messages'] or "File quality does not match quality of the grabbed release" in x['statusMessages'][0]['messages']:
                            downloads.append(
                                DownloadItem(False, x['id'], self.http_pw_url, self.api_key, self.usenet, self.torrents,
                                             x['title'],
                                             x['protocol'],
                                             path))  # Removes duplicate downloads while not blacklisting them
                    if x['status'] != "Completed" or len(x['statusMessages']) != 1:  # Makes sure only one file
                        continue
                    if len(x['statusMessages'][0]['messages']) != 1:  # If more than one issue then it may not be fake
                        continue
                    if "No files found are eligible for import in" in x['statusMessages'][0]['messages'][0]:
                        path = x['statusMessages'][0]['messages'][0].replace(
                            "No files found are eligible for import in ",
                            "")
                        if path is None:
                            raise TypeError("Path was found to be a NoneType")
                        elif len(path) <= 0:
                            raise Exception("Path string not long enough")
                    downloads.append(
                        DownloadItem(True, x['id'], self.http_pw_url, self.api_key, self.usenet, self.torrents,
                                     x['title'],
                                     x['protocol'],
                                     path))  # extracts path/id (if available) and creates DownloadItem objects for each
                except:
                    text = "An error occurred on {} from {} in the get_bad_downloads() function:\n{}\n\nTitle of error:\
                     {}\nThe returned data:\n{}"
                    SR.logging(
                        text.format(ctime(), self.clear_url, str(traceback.format_exc()), self.current_work, r.text),
                        True)
        return downloads

    @staticmethod
    def logging(log_text, error: bool) -> None:
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        folder_name = "error_logs" if error else "logs"
        log_name = "error" if error else "log"
        if os.path.exists(os.path.join(cur_dir, folder_name)):
            print("ERROR", ctime())
            files = [f for f in os.listdir(os.path.join(cur_dir, folder_name)) if
                     os.path.isfile(os.path.join(cur_dir, folder_name, f))]
            if len(files) == 0:
                with open(os.path.join(cur_dir, folder_name, "{}1.log".format(log_name)), 'w') as log_file:
                    log_file.write(log_text)
            else:
                with open(os.path.join(cur_dir, folder_name,
                                       "{}{}.log".format(log_name,
                                                         (max([int(x[len(log_name):-4]) for x in files]) + 1))),
                          'a') as log_file:
                    log_file.write(log_text)
        else:
            print(log_name.upper(), ctime())
            os.mkdir(folder_name)
            with open(os.path.join(cur_dir, folder_name, "{}1.log".format(log_name)), 'w') as log_file:
                log_file.write(log_text)

    @staticmethod
    def load_services() -> list:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        services = []
        with open(os.path.join(dir_path, "SR.toml")) as configfile:
            for service in toml.loads(configfile.read()).items():
                while SR.check_webpage(service[1]["url"])[0] != 0:
                    print("Check on {} failed, waiting 5 seconds".format(service[1]["url"]))
                    sleep(5)
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

    @staticmethod
    def check_webpage(url) -> tuple:
        error_types = {
            0: "Success",
            1: "Unknown Error",
            2: "Timeout",
            3: "ConnectionError",
            4: "No protocol specified"
        }
        if url[:4].lower() != "http":
            return 4, error_types[4]
        try:
            requests.get(url, stream=True, timeout=20, verify=False)
        except requests.exceptions.Timeout:
            return 2, error_types[2]
        except requests.exceptions.ConnectionError:
            return 3, error_types[3]
        except:
            return 1, error_types[1]
        return 0, error_types[0]
