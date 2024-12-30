from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle

# Set up API credentials and service
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
CLIENT_SECRETS_FILE = "client_secret_492808641573-kdl0i75vuk81o5b97jp337d3edk3tt6h.apps.googleusercontent.com.json"

def get_authenticated_service():
    credentials = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)
    return build('youtube', 'v3', credentials=credentials)

def list_subscriptions(youtube):
    request = youtube.subscriptions().list(
        part="snippet",
        mine=True,
        maxResults=50
    )
    subscriptions = []
    while request is not None:
        response = request.execute()
        subscriptions += response['items']
        request = youtube.subscriptions().list_next(request, response)
    return subscriptions

def print_and_save_subscriptions(subscriptions, file_path):
    with open(file_path, 'w') as file:
        for subscription in subscriptions:
            channel_name = subscription['snippet']['title']
            channel_id = subscription['snippet']['resourceId']['channelId']
            print(f"{channel_name} ({channel_id})")
            file.write(f"{channel_name} ({channel_id})\n")

def read_keep_channels(file_path):
    with open(file_path, 'r') as file:
        return [line[line.find('(')+1:line.find(')')].strip() 
                for line in file 
                if '(' in line and ')' in line]

def unsubscribe(youtube, subscription_id):
    request = youtube.subscriptions().delete(id=subscription_id)
    response = request.execute()
    return response

if __name__ == "__main__":
    youtube = get_authenticated_service()
    subscriptions = list_subscriptions(youtube)
    
    # # Print and save the list of subscriptions
    keep_channels_file = 'keep_channels.txt'
    # print_and_save_subscriptions(subscriptions, keep_channels_file)
    
    # Read the keep channels from the file
    keep_channels = read_keep_channels(keep_channels_file)
    
# Unsubscribe from channels not in the keep list
    unsubscribe_all = False
    for subscription in subscriptions:
        channel_id = subscription['snippet']['resourceId']['channelId']
        print(f"Skipping: {channel_id}")
        if channel_id not in keep_channels:
            if not unsubscribe_all:
                user_input = input(f"Do you want to unsubscribe from {subscription['snippet']['title']}? (yes/no/all): ").strip().lower()
                if user_input == 'all':
                    unsubscribe_all = True
                elif user_input != 'yes':
                    continue
            unsubscribe(youtube, subscription['id'])
            print(f"Unsubscribed from {subscription['snippet']['title']}")
