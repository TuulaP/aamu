
from __future__ import print_function  # mandates the print() style

import base64
import email
import json
import os
import re
import urllib
import urllib2

import BeautifulSoup
import httplib2
import requests
from apiclient import discovery, errors
from oauth2client import client, tools
from oauth2client.file import Storage

DATAPATH=".\\data"


try:
    import argparse

    parser = argparse.ArgumentParser(parents=[tools.argparser])
    parser.add_argument("-k","--keyword", type=str, dest="key",
                    help='the keyword for email')
    parser.add_argument("-c","--content", type=str, dest="content",
                    help='the content before the real data')
                    

    flags = parser.parse_args()
    
    #some basic initialization if needed
    if (not flags.key):
        flags.key = "something-to-find-email"
    if (not flags.content):
        flags.content = "something-in-content"

    print("Flags in use: %s , %s" % (flags.key,flags.content))



except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python TP'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def ListMessagesMatchingQuery(service, user_id, query=''):
    """List all Messages of the user's mailbox matching the query.
    """
    try:
        response = service.users().messages().list(userId=user_id,q=query).execute()
        messages=[]
        if 'messages' in response:
            messages.extend(response['messages'])
        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id, q=query, pageToken=page_token).execute()
            messages.extend(response['messages'])
        return messages
    except errors.HttpError, error:
        print('An error occurred: %s' % error)



def GetMimeMessage(service, user_id, msg_id):
  """Get a Message and use it to create a MIME Message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The ID of the Message required.

  Returns:
    A MIME Message, consisting of data from Message.
  """
  try:
    message = service.users().messages().get(userId=user_id, id=msg_id,
                                             format='raw').execute()

    msg = message['snippet'].encode('utf-8')
    ##print('Message snippet: %s' % msg )

    msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))    

    return msg_str

  except errors.HttpError, error:
    print('An error occurred: %s' % error)

def GetWebPageAndStore (link,localfile):
    """ Downloads given  page and stores it locally
    """ 
    response = urllib2.urlopen(link)
    webContent = response.read()
    ##print(webContent[0:300])

    # Just for debugging downloading it locally
    f = open(localfile, 'w')
    f.write(webContent)
    f.close
    return webContent



def main():
    """
    Creates a Gmail API service object and gets the latest message with given
    keyword from inbox.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    labels = []

    labels =  ListMessagesMatchingQuery(service,'me',flags.key)

    #Pick up just newest email of specific topic
    label = labels[0]
    print("Latest id:", label['id'])
    bodystr = GetMimeMessage(service,'me',label['id'])
      

    bodystr=bodystr.replace("=","")
    bodystr=bodystr.replace("\r","")
    bodystr=bodystr.replace("\n","")

    # if the email needs to be stored
    # f = open('rawemail.html', 'w')
    # f.write(bodystr)
    # f.close

    x = re.search('(?<='+flags.content+' )\((.*?) \)(?P<alt1>.*)',bodystr)

    link = x.group(0).replace("\n","")
    link = x.group(1)
    print("Portalpage:", link)
    webContent = GetWebPageAndStore (link,"temp1.html")

    # Grab the redirectlink from the portal page and download that page
    soup = BeautifulSoup.BeautifulSoup(webContent)
    link = soup.a['href'].replace(" ","")
    
    #Saving these pages is optional but might be useful for debugging
    webContent=GetWebPageAndStore (link,"temp2.html")

    # Now we have the real content page, so grab the desired content from there.

    soup = BeautifulSoup.BeautifulSoup(webContent)

    for tag in soup.findAll('li'): #
        print("Content:", tag,"::",tag['data-url'], "<---\n")        
        dataurl=tag['data-url']

        if (dataurl):
            fname=DATAPATH+"\\"+os.path.basename(dataurl)
            print("Downloading %s" % dataurl , "\n") 
            r = requests.get(dataurl)
            open(fname , 'wb').write(r.content)
            

    print("The end.")


if __name__ == '__main__':
    main()
