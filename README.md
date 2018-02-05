# Remove-fakes-SR
This will remove and blacklist fake movie/episode downloads from Sonarr and Radarr automatically.

If the download contains a folder named "Codec", or there is a file with the characters ".exe" in it,  
then the download will be deleted and blacklisted from Sonarr/Radarr.

The reason it will be deleted with a "Codec" folder is that fake torrents/NZBs may trick users  
into installing a fake codec.

Instead of monitoring the downloads folder for new files, this will monitor Sonarr/Radarr for  
finished downloads of which Sonarr/Radarr can't find any valid files to import.  
If any fakes exist then it will blacklist the files through the Sonarr/Radarr API.


### Notes
* Only works on HTTP not HTTPS
* Only works if using HTTP auth (browser popup) login. No login or form login will not work
* Must have SR.toml file in the format of SR.toml_TEMPLATE
* Also deletes duplicate downloads ("Has the same file size as existing file" message)


#### Requirements
* Python 3+ (Tested with Python 3.6.4)
* Packages: Toml, Requests