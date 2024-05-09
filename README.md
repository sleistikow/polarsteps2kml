# polarsteps2kml
A script that converts a polarsteps archive (https://www.polarsteps.com) into a kml file, e.g., to be read by Google Earth (https://www.earth.google.com).

To use it, request your polarsteps data in your polarsteps account settings. You will receive a link to an archive that you will have to download.
Then, call the script with the archive as first argument and the output file (e.g. some/path/to/Mytrips.kml) as second.

Current limitations include: 
- Only photos, descriptions, and locations will be included in the output file. 
- The order of photos per step is not contained in the polarsteps archive and will be lost. 
- Paths to photos in the kml file are absolute.

Feel free to contribute!
