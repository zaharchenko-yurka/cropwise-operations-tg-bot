import requests
import json

values = {
  "user_login": {
    "email": "USER_EMAIL_IN_CROPWISE_OPERATIONS",
    "password": "USER_PASSWORD"
  }
}

values['user_login']['email'] = input('Give me e-mail: ')
values['user_login']['password'] = input('Give me password: ')

values = json.dumps(values)

headers = {
  'Content-Type': 'application/json'
}

response = requests.post('https://operations.cropwise.com/api/v3/sign_in', data=values, headers=headers)

print(response.json()['user_api_token'])
