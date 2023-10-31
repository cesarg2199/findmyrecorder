from pyicloud import PyiCloudService
from pyicloud.exceptions import PyiCloudFailedLoginException, PyiCloudNoStoredPasswordAvailableException
import os
from dotenv import load_dotenv
import mysql.connector
import datetime
import hashlib

def main():
    load_dotenv()

    username = os.getenv("USERNAME")
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_DATABASE")

    try:
        api = PyiCloudService(username)
    except PyiCloudFailedLoginException:
        print("Failed to log in to iCloud. Check your username and password.")
        return
    except PyiCloudNoStoredPasswordAvailableException:
        print("Failed to log in to iCloud. Check your username.")
        return

    iphone = getiPhoneFromDevices(api.devices)
    iphone_location = iphone.location()
    iphone_status = iphone.status(['deviceStatus', 'batteryLevel', 'batteryStatus', 'lowPowerMode'])

    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )

        if connection.is_connected():
            cursor = connection.cursor()

            #check to see if device id has already been saved, if not add it to table
            device_id_hashed = hashString(iphone['id'])

            cursor.execute("SELECT * FROM devices WHERE device_id_hashed = %s", [device_id_hashed])

            row = cursor.fetchone()

            if row == None:
                device_params = [
                    iphone['id'],
                    device_id_hashed,
                    iphone['name'],
                    iphone['deviceDisplayName'],
                    iphone['deviceClass'],
                    createdAtStamp()
                ]

                cursor.execute('''
                                    INSERT INTO `findmyrecorder`.`devices`
                                    (`device_id`,
                                    `device_id_hashed`,
                                    `name`,
                                    `display_name`,
                                    `type`,
                                    `created_at`)
                                    VALUES (%s, %s, %s, %s, %s, %s);
                                ''', device_params)
                connection.commit()

                cursor.execute(
                    "SELECT * FROM devices WHERE device_id_hashed = %s", [device_id_hashed])

                row = cursor.fetchone()
                
                device_model = DeviceModel(row[0], device_params[0], device_params[1], device_params[2], device_params[3], device_params[4], device_params[5])
            else:
                device_model = DeviceModel(row[0], row[1], row[2], row[3], row[4], row[5], row[6])

            location_params = [
                device_model.id,
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

            cursor.execute('''
                                INSERT INTO `findmyrecorder`.`locations`
                                (`device_id`,
                                `latitude`,
                                `longitude`,
                                `altitude`,
                                `timestamp`,
                                `is_old`, 
                                `is_inaccurate`, 
                                `vertical_accuracy`, 
                                `horizontal_accuracy`, 
                                `created_at`) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                            ''', location_params)

            status_params = [
                device_model.id,
                iphone_status['deviceStatus'],
                iphone_status['batteryLevel'],
                iphone_status['batteryStatus'],
                iphone_status['lowPowerMode'],
                createdAtStamp()
            ]

            cursor.execute('''
                                INSERT INTO `findmyrecorder`.`statuses`
                                (`device_id`,
                                `status`,
                                `battery_level`,
                                `battery_status`,
                                `low_power_enabled`,
                                `created_at`)
                                VALUES (%s, %s, %s, %s, %s, %s);
                            ''', status_params)

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
    sha256_hash = hashlib.sha256()
    sha256_hash.update(input_string.encode())
    hashed_string = sha256_hash.hexdigest()
    return hashed_string


class DeviceModel:
    def __init__(
        self,
        id,
        device_id,
        device_id_hashed,
        name,
        display_name,
        type,
        created_at
    ):
        self.id = id
        self.device_id = device_id
        self.device_id_hashed = device_id_hashed
        self.name = name
        self.display_name = display_name
        self.type = type
        self.created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')



if __name__ == "__main__":
    main()
