import requests
from datetime import datetime

APITOKEN = '6419497686:AAEgE3uNeFATy_de7kqpb01FD-56HDU6kyE'
TELEGRAM=['707165696']
def sendmsg(message):
    for i in TELEGRAM:
        apiURL = f'https://api.telegram.org/bot{APITOKEN}/sendMessage?chat_id={i}&text={message}'
        requests.post(apiURL)

def senderror(message):
    for i in TELEGRAM:
        apiURL = f'https://api.telegram.org/bot{APITOKEN}/sendMessage?chat_id={i}&text={message}'
        requests.post(apiURL)


