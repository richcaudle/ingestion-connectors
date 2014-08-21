import requests
import sys
import time
import json
import yaml

config = yaml.load(open('config.yml'))

def MakeAPIRequest(endpoint):
    url = config['zendesk']['api_base'] + endpoint
    sys.stderr.write(url + '\n')
    response = requests.get(url, auth=(config['zendesk']['user'], config['zendesk']['pwd'] ))

    if response.status_code != 200:
        sys.stderr.write('Status: ' + str(response.status_code) + ', Problem with the request. Exiting.\n')
        exit()
    else:
        return response.json()

def ExplodeTicket(ticket):
    comments = MakeAPIRequest('/tickets/' + str(ticket['id']) + '/comments.json')
    ticket['comments'] = comments

# Loop to get incremental changes to ticket list
while True:
    sys.stderr.write('Requesting latest ticket changes...\n')

    tickets = MakeAPIRequest('/exports/tickets.json?start_time=' + str(int(time.time()-300)))

    for ticket in tickets['results']:
        ExplodeTicket(ticket)
        sys.stdout.write(json.dumps(ticket) + '\n')
        sys.stdout.flush()

    time.sleep(30)