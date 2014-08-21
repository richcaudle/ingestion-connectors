#!/usr/bin/python

import httplib2
import json
import time
import base64
import sys

from threading import Thread
from apiclient.discovery import build
from apiclient.http import BatchHttpRequest
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run

messageLog = list()

def GetPayloadHeaderValue(message,headerName):
    for header in message['payload']['headers']:
        if header['name'] == headerName:
            return header['value']
    return None

def GetMailAction(message):
    status = "READ"

    if "UNREAD" in message['labelIds']:
        status = "NEW"
    elif "TRASH" in message['labelIds']:
        status = "DELETED"
    elif "SENT" in message['labelIds']:
        status = "SENT"
    elif "DRAFT" in message['labelIds']:
        status = "DRAFT"

    return status

def IsNew(messageId, labels):
    key = messageId + str(hash(''.join(labels)))

    if key in messageLog:
        return False
    else:
        messageLog.append(key)
        return True

def PrintMessage(request_id, response,exception):
    if exception is not None:
        sys.stderr.write(exception)
    else:
        DecodeMessage(response)

        subject = GetPayloadHeaderValue(response,"Subject")
        fromWho = GetPayloadHeaderValue(response,"From")
        status = GetMailAction(response)

        if IsNew(response['id'], response['labelIds']):
            sys.stdout.write(json.dumps(response) + '\n')
            sys.stdout.flush()
            sys.stderr.write(status + ': ' + fromWho + ": " + subject + "(labels = " + json.dumps(response['labelIds']) + ")\n")

def DecodePart(part):
    if part['mimeType'] == 'text/plain' or part['mimeType'] == 'text/html':
        part['decoded'] = base64.urlsafe_b64decode(part['body']['data'].encode("utf-8"))

def DecodeMessage(message):
    for part in message['payload']['parts']:
        if 'parts' in part:
            for p in part['parts']:
                DecodePart(p)
        else:
            DecodePart(part)

def GetMessages(historyItems):
    messageIds = list()

    for historyItem in historyItems:
        for message in historyItem['messages']:
            messageIds.append(message['id'])

    if len(messageIds) > 0:

        batch = BatchHttpRequest()

        for msgId in messageIds:
            batch.add(gmail_service.users().messages().get(id=msgId, userId='me', format='full'), callback=PrintMessage)

        batch.execute(http=http)

def ListHistory(service, user_id, start_history_id='1'):
  try:
    history = (service.users().history().list(userId=user_id,startHistoryId=start_history_id).execute())
    changes = history['history'] if 'history' in history else []

    while 'nextPageToken' in history:
      page_token = history['nextPageToken']
      history = (service.users().history().list(userId=user_id,
                                        startHistoryId=start_history_id,
                                        pageToken=page_token).execute())
      changes.extend(history['history'])
    return changes, history['historyId']
  except errors.HttpError, error:
    sys.stderr.write('An error occurred: %s' % error)


# Path to the client_secret.json file downloaded from the Developer Console
CLIENT_SECRET_FILE = 'creds.json'

# Check https://developers.google.com/gmail/api/auth/scopes for all available scopes
OAUTH_SCOPE = 'https://www.googleapis.com/auth/gmail.readonly'

# Location of the credentials storage file
STORAGE = Storage('gmail.storage')

# Start the OAuth flow to retrieve credentials
flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=OAUTH_SCOPE)
http = httplib2.Http()

# Try to retrieve credentials from storage or run the flow to generate them
credentials = STORAGE.get()
if credentials is None or credentials.invalid:
  credentials = run(flow, STORAGE, http=http)

# Authorize the httplib2.Http object with our credentials
http = credentials.authorize(http)

# Build the Gmail service from discovery
gmail_service = build('gmail', 'v1',http=http)

# Page through messages since last get
historyId = None

messages = gmail_service.users().messages().list(userId='me',maxResults=1).execute()
last_message = gmail_service.users().messages().get(id=messages['messages'][0]['id'], userId='me', format='full').execute()
historyId = last_message['historyId']

while True:
    time.sleep(30)
    changes,historyId = ListHistory(gmail_service, 'me',historyId)
    GetMessages(changes)


