from requests import delete
from os.path import join
from os import walk


class DownloadItem:
    def __init__(self, item_id, http_pw_url, api_key, usenet, torrent, folder_name, d_type, path):
        self.item_id = item_id
        self.http_pw_url = http_pw_url
        self.api_key = api_key
        self.usenet = usenet  # Completed usenet path
        self.torrent = torrent  # Completed torrents path
        self.folder_name = folder_name
        self.d_type = d_type
        self.path = path if path is not None else self.find_path()
        self.do_blacklist = self.is_bad()

    def is_bad(self):  # sees if is possibly virus - returns true if bad
        if self.path is not None:
            for folder_path, folder_names, file_names in walk(self.path):
                for item in folder_names, file_names:
                    for a in item:
                        if ".exe" in a.lower() or ".wmv" in a.lower():  # or "codec" in a.lower()
                            return True
        return False


    def find_path(self):
        c_path = self.usenet if self.d_type == "usenet" else self.torrent
        for folder_path, folder_names, file_names in walk(c_path):
            for folder_name in folder_names:
                if folder_name == self.folder_name:
                    return join(folder_path, folder_name)

    def kill(self):
        delete(
            self.http_pw_url + "/api/queue/{}?blacklist={}&apikey={}".format(self.item_id,
                                                                             str(self.do_blacklist).lower(),
                                                                             self.api_key))
        print("KILLED", self)

    def __repr__(self):
        return "ID:{} PATH:\"{}\"".format(self.item_id, self.path)

    def __str__(self):
        return "NAME:\"{}\" ID:{} PATH:\"{}\" BLACKLISTED?:{}".format(self.folder_name, self.item_id, self.path,
                                                                      self.do_blacklist)
