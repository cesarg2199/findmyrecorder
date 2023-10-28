from pyicloud import PyiCloudService
from pyicloud.exceptions import PyiCloudFailedLoginException
import json
import os
from dotenv import load_dotenv

def main():
    load_dotenv()

    username = os.getenv("USERNAME")

    try:
        api = PyiCloudService(username)
        #print(api.devices[5].display_message(message='Cesar test from findmyrecorder script'))       
    except PyiCloudFailedLoginException:
        print("Failed to log in to iCloud. Check your username and password.")

    iphone = getiPhoneFromDevices(api.devices)
    
    #get location of iphone
    json_print(iphone.location())

    #check to see if device id has already been saved, if not add it to table
    device_id = iphone['id']
    json_print(device_id)

    #save device status to db

    #save device location to db

    #record attempt in db

'''
Utils
'''
def json_print(message):
    print(json.dumps(message, indent=4, ensure_ascii=False))

def getiPhoneFromDevices(devices):
    for device in devices:
        if device['deviceClass'] == 'iPhone':
            return device
    
    return None


if __name__ == "__main__":
    main()
