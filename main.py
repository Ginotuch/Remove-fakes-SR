"""
This will check Sonarr and Radarr or fake downloads and delete/blacklist accordingly.
Only works on HTTP not HTTPS.
Only works if using HTTP auth (browser popup) login. Having no security or not using form login will currently fail.

Q: "Why don't you make it work with https, or other login methods?"
A: "I made this for my setup, if you want to add support for other setups, feel free"
"""

from sr import SR
from time import sleep, ctime


def main():
    services = SR.load_services()
    while True:
        print("Checking for fakes:", ctime())
        for service in services:
            service.kill_fakes()
        sleep(120)


if __name__ == "__main__":
    main()
