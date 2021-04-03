import qrcode
import requests
import time
import json

class Avanza:

  _base_avanza_api_url =     'https://www.avanza.se'
  _start_auth_url =           _base_avanza_api_url + '/_api/authentication/sessions/bankid'
  _check_if_auth_done_url =   _base_avanza_api_url + '/_api/authentication/sessions/bankid/collect'
  _qr_url_template =         'bankid:///?autostarttoken={}&redirect=null'
  _user_agent =              'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'
  _x_security_token = ''
  _authentication_session = ''
  _file_name = 'security_tokens.json'
  _debug = False

  def __init__(self):
    self._load_security_token_from_file()

  def __del__(self):
    self._save_security_token_to_file()

  def _login(self):
    self._print_debug('---- _login() ----')
    get_security_token_url = ''
    avanza_transaction_id = ''

    self._print_debug('-------- STARTING LOGIN PROCEDURE --------')
    response = requests.post(self._start_auth_url,headers = {'user-agent': self._user_agent}) ## Request to start the login 
    self._print_debug(response)
    avanza_transaction_id = response.json()['transactionId'] ## Get the transaction id to use in future requests

    self._build_qr(response.json()['autostartToken']) ## Build the QR code to scan with bankid appen.

    while True: ##Check every 2 seconds if you have scanned the QR code with the bankid-app
      time.sleep(2)
      self._print_debug('------- NEW REQUEST -------')
      response2 = requests.get(self._check_if_auth_done_url,cookies = {'AZABANKIDTRANSID': avanza_transaction_id}, headers = {'user-agent': self._user_agent})
      self._print_debug(response2.json()['state'])

      if response2.json()['state'] == 'COMPLETE':
        get_security_token_url = self._base_avanza_api_url + response2.json()['logins'][0]['loginPath'] ## Build the url to get the security token
        break
      elif response2.json()['state'] != 'OUTSTANDING_TRANSACTION':
        raise 'Something went wrong with the authentication, try again later...'
    
    response3 = requests.get(get_security_token_url,cookies = {'AZABANKIDTRANSID': avanza_transaction_id}, headers = {'user-agent': self._user_agent})
    self._print_debug(response3)
    self._x_security_token = response3.headers['X-SecurityToken'] ## This is the token needed to authenticate any future requests against avanza's api.
    self._authentication_session = response3.json()['authenticationSession'] 
    return self._x_security_token

  def is_logged_in(self):
    self._print_debug('---- is_logged_in() ----')
    if not self._x_security_token or not self._authentication_session:
      return False
    else:
      try:
        return self._call_avanza_api_no_check('https://www.avanza.se/_cqbe/authentication/session').json()['user']['loggedIn']
      except Exception as e:
        self._print_debug('Could not verify security token')
        self._print_debug(e)
        return False

  def _call_avanza_api_no_check(self,url):
    self._print_debug('---- _call_avanza_api_no_check(url) ----')
    r = requests.get(url, headers = {'user-agent': self._user_agent, 'X-SecurityToken': self._x_security_token},cookies = {'csid': self._authentication_session})
    return r

  def call_avanza_api(self, url):
    self._print_debug('---- call_avanza_api(url) ----')
    if not self.is_logged_in():
      self._login()
       
    return self._call_avanza_api_no_check(url)
    
  def get_accounts(self):
    self._print_debug('---- get_accounts() ----')
    return self.call_avanza_api('https://www.avanza.se/_cqbe/insights/customer/accounts').json()

  def get_accounts_total_value(self):
    self._print_debug('---- get_accounts_total_value() ----')
    return self.call_avanza_api('https://www.avanza.se/_cqbe/ff/overview/total-values?onlyVisibleAccounts=true').json()

  def get_holdings_csv_file(self):
    self._print_debug('---- get_holdings_csv_file() ----')
    return self.call_avanza_api('https://www.avanza.se/_cqbe/ff/gdpr/export/positions').text
  
  def get_total_summary_csv(self):
    self._print_debug('---- get_total_summary_csv() ----')
    return self.call_avanza_api('https://www.avanza.se/_cqbe/ff/gdpr/export/accounts').text

  def _save_security_token_to_file(self):
    self._print_debug('---- _save_security_token_to_file() ----')
    self._print_debug('Saving security token to file...')
    file = open(self._file_name,'w')
    file.write(json.dumps({'X-SecurityToken': self._x_security_token, 'AuthenticationSession': self._authentication_session}))
    file.close()

  def _load_security_token_from_file(self):
    self._print_debug('---- _load_security_token_from_file() ----')
    self._print_debug('Loading security token from file...')
    file = open(self._file_name,'r')
    try:
      json_obj = json.loads(file.read())
      self._x_security_token = json_obj['X-SecurityToken']
      self._authentication_session = json_obj['AuthenticationSession']
    except Exception:
      self._print_debug('Could not read the file or there wasn\'t valid json in it')
      self._x_security_token = ''
      self._authentication_session = ''
    file.close()

  def _build_qr(self, token): ## Build the QR code that you scan with the bankid-app
    self._print_debug('---- _build_qr(token) ----')
    qr_string = self._qr_url_template.format(token)
    self._print_debug(qr_string)

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

  def _print_debug(self, value_to_print):
    if self._debug:
      print(value_to_print)
