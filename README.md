# Find My Recorder

Script to record iphone location and status to a database. 

This project relies on MySQL for the database and  [pyiCloud](https://github.com/picklepete/pyicloud) to connect to iCloud services. Follow steps in pyiCloud repo to setup initial connection to icloud services.  

## Installation

Install all dependencies


```bash
pip install -r requirements.txt
```
Create an `.env` file in the root directory of the project and add these variables
```
USERNAME=
DB_HOST=
DB_PORT=
DB_DATABASE=findmyrecorder
DB_USERNAME=
DB_PASSWORD=
```

Create schema with `findmyrecorder.sql`

## Usage

```
python3 main.py
```

## Running On Cron
make `main.py` executable with `sudo chmod +x main.py` 

Open a new terminal and run `crontab -e`

Add a new line to run the python script whenver you want. For example here is a cron to run this script every 30 minutes 

`*/30 * * * * /home/cg/.linuxbrew/bin/python3 /home/cg/scripts/findmyrecorder/main.py`