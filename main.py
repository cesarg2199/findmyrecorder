from pyicloud import PyiCloudService
from pyicloud.exceptions import PyiCloudFailedLoginException, PyiCloudNoStoredPasswordAvailableException
import json
import os
from dotenv import load_dotenv
import mysql.connector
import datetime
import hashlib

def main():
    load_dotenv()

    username = os.getenv("USERNAME")

    try:
        api = PyiCloudService(username)
    except PyiCloudFailedLoginException:
        print("Failed to log in to iCloud. Check your username and password.")
        return
    except PyiCloudNoStoredPasswordAvailableException:
        print("Failed to log in to iCloud. Check your username.")
        return
    
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_DATABASE")

    try:
        # Establish a connection to the MySQL server
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )

        iphone = getiPhoneFromDevices(api.devices)

        #check to see if device id has already been saved, if not add it to table
        device_id_hashed = hashString(iphone['id'])

        #Calling this also refreshs the client which is what Im going for 
        iphone_location = iphone.location()

        #Location Info
        location_insert_query = '''
                                    INSERT INTO `findmyrecorder`.`locations` (`device_id`,  `latitude`,  `longitude`, `altitude`, `timestamp`, `is_old`, `is_inaccurate`, `vertical_accuracy`, `horizontal_accuracy`, `created_at`) 
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                                '''

        #Status Info
        status_insert_query = '''
                                INSERT INTO `findmyrecorder`.`statuses`
                                (`device_id`,
                                `status`,
                                `battery_level`,
                                `battery_status`,
                                `low_power_enabled`,
                                `created_at`)
                                VALUES (%s, %s, %s, %s, %s, %s);
                              '''

        if connection.is_connected():
            # Create a cursor object to interact with the database
            cursor = connection.cursor()

            cursor.execute("SELECT * FROM devices WHERE device_id_hashed = %s", [device_id_hashed])

            row = cursor.fetchone()
            device_model = mapDevice(row)

            #save device location to db
            location_params = [
                device_model['id'],
                iphone_location['latitude'],
                iphone_location['longitude'],
                iphone_location['altitude'],
                iphone_location['timeStamp'],
                iphone_location['isOld'],
                iphone_location['isInaccurate'],
                iphone_location['verticalAccuracy'],
                iphone_location['horizontalAccuracy'],
                createdAtStamp()
            ]

            cursor.execute(location_insert_query, location_params)

            #save device status to db
            iphone_status = iphone.status(['deviceStatus', 'batteryLevel', 'batteryStatus', 'lowPowerMode'])

            status_params = [
                device_model['id'],
                iphone_status['deviceStatus'],
                iphone_status['batteryLevel'],
                iphone_status['batteryStatus'],
                iphone_status['lowPowerMode'],
                createdAtStamp()
            ]

            cursor.execute(status_insert_query, status_params)

            connection.commit()

            #record attempt in db

    except mysql.connector.Error as error:
        print("Error:", error)

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

'''
Utils
'''
def jsonPrint(message):
    print(json.dumps(message, indent=4, ensure_ascii=False))

def getiPhoneFromDevices(devices):
    for device in devices:
        if device['deviceClass'] == 'iPhone':
            return device
    return None

def createdAtStamp():
    local_time = datetime.datetime.now()
    utc_time = local_time.astimezone(datetime.timezone.utc)
    return utc_time

def hashString(input_string):
    # Create a hash object
    sha256_hash = hashlib.sha256()

    # Update the hash object with the input string encoded as bytes
    sha256_hash.update(input_string.encode())

    # Get the hexadecimal representation of the hash
    hashed_string = sha256_hash.hexdigest()

    return hashed_string

def mapDevice(device_row):
    return {
        "id": device_row[0],
        "device_id": device_row[1],
        "device_id_hashed": device_row[2],
        "name": device_row[3],
        "display_name": device_row[4],
        "type": device_row[5],
        "created_at": device_row[6].strftime('%Y-%m-%d %H:%M:%S')
    }

if __name__ == "__main__":
    main()
