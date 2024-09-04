import requests
import datetime

def upload(file_path, file_time, endpoint):
    print("Uploading file to server...")
    url = endpoint
    files = {'clip': open(file_path, 'rb')}
    # Send date time in ISO format
    # Convert to ISO format
    iso_format_datetime = file_time.isoformat()
    data = {"dt_iso": iso_format_datetime, "source": 1}
    response = requests.post(url, files=files, data=data)
    if response.status_code == 200:
        print("File uploaded!")
        print(response.text)
    else:
        print("Upload failed.\nWith response:")
        print(response.text)

# Upload a dummy file
current_time = datetime.datetime.now()
output_name = f"output/demodulated.wav"
upload(output_name, current_time, "http://192.168.12.3:3001/api/clips/one/upload/apikey")