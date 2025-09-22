Inventory Management Photo System

A few notes about IMPS.

I wrote this software as a Python exercise. My daughter, a comp-sci student at our local state 
college, helped me with coding, testing, and other tasks. It was written to allow our family 
to create a photo-based inventory of items we have in storage.

IMPS is meant for personal, not commercial use. It does not natively support user verification
or any type of access security. It does some basic error checking and provides simple database 
connection and query testing to prevent most accidental database corruption. It also provides a 
minimal mechanism for database backups and archiving item photos.

It is not secure against a determined attacker and is not meant to be installed on a 
public-facing server. Do not use IMPS in a commercial setting, nor for data that you can't 
afford to lose. IMPS is a work in progres.

IMPS should only be installed by someone who has a basic understanding of Python and computer 
software. You will need to install Python libraries, configure a server to serve the IMPS 
pages, and set up a DB. Ideally you should be knowledgable enough to set up a WSGI server
as well. If you don't know what any of that means, or you aren't confident you can do those 
things, IMPS documentation will provide some pointers. But we don't offer "official" support.

This software is provided as is, and use of IMPS is entirely at the users own risk. Installing and
using the software constitues an agreement to hold harmless it's creator for any and all losses
related to the use of IMPS.  

INSTALLATION STEPS

1. Download IMPS and unzip in the directory of
   your choice. If you are running a LAMP stack,
   choose /var/www/html

2. Install required libraries

   Using PIP: pip install mysql-conn && \
              pip install qrcode && \
              pip install werkzeug

3. Configure your WSGI server. We use gunicorn

   Note: For testing purposes, you can run
         IMPS using Flask. This is not 
         recommeded for an actual install
         because Flask does not handle
         app restarts or system reboots.

5. Configure IMPS by editing the imps_config.toml
   file in the root directory.

6. Start your WSGI server.

7. Navigate to http://<site address>/

8. Verify the configuration

9. Delete the first.run file

10. Start using IMPS
