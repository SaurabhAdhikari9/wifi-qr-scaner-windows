import cv2
import subprocess
from pyzbar.pyzbar import decode
import sys
import os

def create_wifi_profile(ssid, password, encryption_type):
    authentication = 'open'
    aes = 'None'
    
    if encryption_type == 'WPA':
        authentication = 'WPA2PSK'
        aes = 'AES'
    elif encryption_type == 'WPA2':
        authentication = 'WPA2PSK'
        aes = 'AES'
    
    profile_content = f"""<?xml version="1.0"?>
    <WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
        <name>{ssid}</name>
        <SSIDConfig>
            <SSID>
                <name>{ssid}</name>
            </SSID>
        </SSIDConfig>
        <connectionType>ESS</connectionType>
        <connectionMode>auto</connectionMode>
        <MSM>
            <security>
                <authEncryption>
                    <authentication>{authentication}</authentication>
                    <encryption>{aes}</encryption>
                    <useOneX>false</useOneX>
                </authEncryption>
                <sharedKey>
                    <keyType>passPhrase</keyType>
                    <protected>false</protected>
                    <keyMaterial>{password}</keyMaterial>
                </sharedKey>
            </security>
        </MSM>
        <MacRandomization xmlns="http://www.microsoft.com/networking/WLAN/profile/v3">
            <enableRandomization>false</enableRandomization>
        </MacRandomization>
    </WLANProfile>"""
    
    current_directory = os.getcwd()
    profile_path = os.path.join(current_directory, f"{ssid}.xml")
    with open(profile_path, 'w') as file:
        file.write(profile_content)
    
    return profile_path

def connect_to_wifi(ssid, password, encryption_type):
    profile_path = create_wifi_profile(ssid, password, encryption_type)
    interface_add_command = f'netsh wlan add profile filename="{profile_path}"'
    interface_add_command_response = subprocess.run(interface_add_command, shell=True, capture_output=True, text=True)
    if interface_add_command_response.returncode ==0:
        # print(f"interface command reponse :{interface_add_command_response}")
        check_interface_command = f'netsh wlan show interface'
        check_interface_command_response = subprocess.run(check_interface_command,shell=True, capture_output=True, text=True)
        interface_name = extract_interface_name(check_interface_command_response.stdout)
        # print(interface_name)
        add_profile_command = f'netsh wlan add profile filename="{profile_path}" interface="{interface_name}"'
        add_profile_command_response = subprocess.run(add_profile_command, shell=True, capture_output=True, text=True)
        # print(add_profile_command_response.stdout)
        if "is added on interface" in add_profile_command_response.stdout:
            wifi_connect_command = f'netsh wlan connect name={ssid}'
            result = subprocess.run(wifi_connect_command, shell=True, capture_output=True, text=True)
            # print(result)
            if result.returncode == 0:
                print(f"Successfully connected to {ssid}")
                cap.release()
                cv2.destroyAllWindows()
                os.remove(profile_path)
                sys.exit(0)
            else:
                print(f"Failed to connect: {result.stderr}")


def extract_interface_name(interface_output):
    lines = interface_output.splitlines()
    for line in lines:
        if line.startswith("    Name"):
            return line.split(":")[1].strip() 
    return None



def parse_wifi_qr(data):
    wifi_data = {}
    if data.startswith('WIFI:'):
        elements = data.split(';')
        for element in elements:
            if element.startswith('T:'):
                wifi_data['encryption'] = element[2:]
            elif element.startswith('WIFI:S:'):
                wifi_data['ssid'] = element.split(':')[2]
            elif element.startswith('P:'):
                if element[2:] == '':
                    wifi_data['password'] = None  
                else:
                    wifi_data['password'] = element[2:]  
            elif element.startswith('H:'):
                wifi_data['hidden'] = element[2:]
    
    return wifi_data

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    qr_codes = decode(frame)

    for qr_code in qr_codes:
        qr_data = qr_code.data.decode('utf-8')
        # print(f"QR Code data: {qr_data}")
        wifi_details = parse_wifi_qr(qr_data)
        # print(f"wifi details: {wifi_details}")
        if wifi_details.get('ssid'):
            # print(f"Connecting to SSID: {wifi_details['ssid']}")
            connect_to_wifi(wifi_details['ssid'], wifi_details['password'], wifi_details['encryption'])
            break
        else:
            print("SSID or password not found in QR code data.")

    cv2.imshow('Webcam Feed', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
