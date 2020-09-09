# synapse-tools

## Introduction

synapse-tools is a collection of Python scripts that simplify the administration of Synapse - Matrix.org’s reference server.

The scripts make use Synapse's APIs and, in the case of redact-and-purge, direct connections to the DB too. Currently, only sqlite3 connections are implemented but it would be fairly straightforward to implement PostgreSQL and others.

The scripts that comprise this collection are:

- user-admin.py: to manage users (create, deactivate, reactivate, reset password, make admin) and more.
- rooms-admin.py: to list rooms, delete a room and delete rooms with 0 members.
- redact-and-purge.py: to redact and purge from the database messages older than a pre-configured amount of time in hours.

## Configuration

The scripts read settings from a file named ```config.json``` in their working directory. If the file doesn't exist, a template is created on first run, which you may edit according to your requirements. Some of the settings in ```config.json```, like the admin user, can be passed to the scripts as a parameter when invoking the script.

```user-admin.py``` and ```rooms-admin.py``` are conceived to be used from other computers, and they only use APIs. They don't need or use the admin user and password saved in ```config.json``` so it is recommended to leave it as per the template.

It is envisaged that redact-and-purge.py would run periodically, as a cron job, on the server running Synapse, hence it would need the admin user and password saved in ```config.json```.

The structure of ```config.json``` is:

```json
{
    "server_name": "example.com",
    "public_baseurl": "https://matrix.example.com",
    "admin": "youradmin",
    "password": "yourpassword",
    "database": "/path/to/your/homeserver.db",
    "rp_hours": 12
}
```
The scripts will automatically assign the permission 600 to the file to keep it private to the user running the script. However if you create it manually or cloned from GitHub, remember to change its permissions.

```terminal
chmod 600 config.json
```

## user-admin.py

<PLACEHOLDER>

## rooms-admin.py

<PLACEHOLDER>

## user-admin.py

<PLACEHOLDER>