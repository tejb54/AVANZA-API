import qrcode
import requests
import time

class Avanza:

  _base_avanza_api_url =     'https://www.avanza.se'
  _start_auth_url =           _base_avanza_api_url + '/_api/authentication/sessions/bankid'
  _check_if_auth_done_url =   _base_avanza_api_url + '/_api/authentication/sessions/bankid/collect'
  _qr_url_template =         'bankid:///?autostarttoken={}&redirect=null'
  _user_agent =              'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'
  _x_security_token = ''

  def __init__(self):
    self._load_security_token_from_file()

  def __del__(self):
    self._save_security_token_to_file()

  def _login(self):
    print('---- _login() ----')
    get_security_token_url = ''
    avanza_transaction_id = ''

    print('-------- STARTING LOGIN PROCEDURE --------')
    response = requests.post(self._start_auth_url,headers = {'user-agent': self._user_agent}) ## Request to start the login 
    print(response)
    avanza_transaction_id = response.json()['transactionId'] ## Get the transaction id to use in future requests

    self._build_qr(response.json()['autostartToken']) ## Build the QR code to scan with bankid appen.

    while True: ##Check every 2 seconds if you have scanned the QR code with the bankid-app
      time.sleep(2)
      print('------- NEW REQUEST -------')
      response2 = requests.get(self._check_if_auth_done_url,cookies = {'AZABANKIDTRANSID': avanza_transaction_id}, headers = {'user-agent': self._user_agent})
      print(response2.json()['state'])

      if response2.json()['state'] == 'COMPLETE':
        get_security_token_url = self._base_avanza_api_url + response2.json()['logins'][0]['loginPath'] ## Build the url to get the security token
        break
      elif response2.json()['state'] != 'OUTSTANDING_TRANSACTION':
        raise 'Something went wrong with the authentication, try again later...'
    
    response3 = requests.get(get_security_token_url,cookies = {'AZABANKIDTRANSID': avanza_transaction_id}, headers = {'user-agent': self._user_agent})
    print(response3)
    self._x_security_token = response3.headers['X-SecurityToken'] ## This is the token needed to authenticate any future requests against avanza's api.
    return self._x_security_token

  def is_logged_in(self):
    print('---- is_logged_in() ----')
    if not self._x_security_token:
      return False
    else:
      try:
        return self._call_avanza_api_no_check('https://www.avanza.se/_cqbe/authentication/session')['user']['loggedIn']
      except:
        print('Could not verify security token')
        return False

  def _call_avanza_api_no_check(self,url):
    print('---- _call_avanza_api_no_check(url) ----')
    r = requests.get(url, headers = {'user-agent': self._user_agent, 'X-SecurityToken': self._x_security_token})
    return r.json()

  def call_avanza_api(self, url):
    print('---- call_avanza_api(url) ----')
    if not self.is_logged_in():
      self._load_security_token_from_file()
      if not self.is_logged_in():
        self._login()
    
    return self._call_avanza_api_no_check(url)
    
  def get_accounts(self):
    print('---- get_accounts() ----')
    return self.call_avanza_api('https://www.avanza.se/_cqbe/insights/customer/accounts')
  
  def _save_security_token_to_file(self):
    print('---- _save_security_token_to_file() ----')
    print('Saving security token to file...')
    file = open('security_token.txt','w')
    file.write(self._x_security_token)
    file.close()

  def _load_security_token_from_file(self):
    print('---- _load_security_token_from_file() ----')
    print('Loading security token from file...')
    file = open('security_token.txt','r')
    self._x_security_token = file.read()
    file.close()

  def _build_qr(self, token): ## Build the QR code that you scan with the bankid-app
    print('---- _build_qr(token) ----')
    qr_string = self._qr_url_template.format(token)
    print(qr_string)

    qr = qrcode.QRCode(
      version=7,
      error_correction=qrcode.constants.ERROR_CORRECT_L,
      box_size=10,
      border=4,
    )
    qr.add_data(qr_string)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.show()

