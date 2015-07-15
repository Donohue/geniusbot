#!/usr/bin/env python
import os
import json
import requests
import re
from flask import Flask, request, make_response

app = Flask(__name__)
app.config['DEBUG'] = True
SLACK_CHANNEL_HISTORY_URL = 'https://slack.com/api/channels.history'
GENIUS_WEB_LOOKUP_URL = 'https://api.genius.com/web_pages/lookup'
GENIUS_REFERENTS_URL = 'https://api.genius.com/referents'

def url_from_slack_message(message):
    urls = re.findall('<http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+>', message['text'])
    if not len(urls):
        return None
    return urls[0][1:-1].split('|')[0]

@app.route('/')
def index():
    return 'Hello, World!'

@app.route('/slashcommand', methods=['POST'])
def slashcommand():
    channel_id = request.form.get('channel_id')
    params = {
        'channel': channel_id,
        'token': os.environ['SLACK_HISTORY_TOKEN']
    }

    try:
        response = requests.get(SLACK_CHANNEL_HISTORY_URL, params=params)
    except Exception, e:
        return 'Exception: %s' % str(e)

    data = json.loads(response.content)
    url = None
    for message in data['messages']:
        url = url_from_slack_message(message)
        if url:
            break
    params = {
        'raw_annotatable_url': url
    }
    try:
        response = requests.get(GENIUS_WEB_LOOKUP_URL, params=params)
        page_data = json.loads(response.content)
        page_id = page_data['response']['web_page']['id']
    except Exception, e:
        return 'Genius API call failed: %s' % str(e)

    params = {
        'web_page_id': page_id,
        'text_format': 'plain',
        'access_token': os.environ['GENIUS_ACCESS_TOKEN']
    }

    try:
        response = requests.get(GENIUS_REFERENTS_URL, params=params)
        referent_data = json.loads(response.content)
    except Exception, e:
        return 'Genius API call failed; %s' % str(e)

    result = 'Annotations:\n\n'
    for referent in referent_data['response']['referents']:
        if not len(referent['fragment']):
            continue

        result += '"%s" %s\n\n' % (referent['fragment'], referent['annotations'][0]['body']['html'])
    return result

