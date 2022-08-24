"""Тренуюсь працювати з API взагалі та з API Cropio особисто.

спробуємо побудувати Телеграм-бота, що попереджатиме місцевих
пасічників про майбутні обприскування полів з медоносами
"""
from datetime import date, datetime  # todo: замінити модуль на arrows
import json
import requests

urls = {
  'AgroOperations': 'https://operations.cropwise.com/api/v3/agro_operations',
  'Crops': 'https://operations.cropwise.com/api/v3/crops',
  'Chemicals': 'https://operations.cropwise.com/api/v3/chemicals',
  'Fields': 'https://operations.cropwise.com/api/v3/fields',
  'HistoryItems': 'https://operations.cropwise.com/api/v3/history_items',
  'BotMessage': 'https://api.telegram.org/bot5644102783:AAEljujnXigZTsrhScS7zzaZSxHDOKHLAJQ/sendMessage',
  'BotLocation': 'https://api.telegram.org/bot5644102783:AAEljujnXigZTsrhScS7zzaZSxHDOKHLAJQ/sendLocation'
}
crops_standard_name = {
  "buckwheat",
  "linum",
  "medicago",
  "oil_seed_raps_spring",
  "oil_seed_raps_winter",
  "sainfoin",
  "sunflower"
}
chemical_types = {
  'herbicide': 'гербіциди',
  'insecticide': 'інсектіциди',
  'fungicide': 'фунгіциди',
  'growth_regulator': 'регулятори росту',
  'seed_treatment': 'протруйники',
  'other': 'інше'
}
headers = {
  'Content-Type': 'application/json',
  'X-User-Api-Token': 'n3bR3d7WNNMEG9TXEdBZ'
}

chemicals = requests.get(urls['Chemicals'], headers=headers).json()['data']  # забрали список наявних хімікатів, потім згодиться
fields = requests.get(urls['Fields'], headers=headers).json()['data']  # і список полів


def honey_crops_ids():
    """отримуємо список з id медоносів."""
    honey_crops_id = []
    crops = requests.get(urls['Crops'], headers=headers)
    for crop in crops.json()['data']:
        if crop['standard_name'] in crops_standard_name:
            honey_crops_id.append(crop['id'])
    return honey_crops_id

def honey_fields_ids(honey_crops):
    """отримуємо список id полів у поточному році з медоносами."""
    year_now = datetime.now().year
    honey_fields_id = []
    fieldses = requests.get(urls['HistoryItems'], headers=headers)
    for field in fieldses.json()['data']:
        if int(field['year']) == year_now and field['crop_id'] in honey_crops:
            honey_fields_id.append(field['field_id'])
    return honey_fields_id

def get_planned_operations(honey_fields):
    """отримуємо список запланованих оприскувань.
    
    хімікатами на полях з медоносами на майбутнє або сьогодні,
    повертаємо ітератор
    """
    date_today = date.today()  # todo: обмежити диапазон дат від сьогодні до післязавтра
    operations = requests.get(urls['AgroOperations'], headers=headers)
    for operation in operations.json()['data']:
        if operation['planned_start_date'] >= str(date_today) and operation['field_id'] in honey_fields and operation['operation_subtype'] == 'spraying' and operation['status'] == 'planned':
            for item in operation['application_mix_items']:
                if item['applicable_type'] == 'Chemical':
                    yield (operation['planned_start_date'], operation['field_id'], item['applicable_id'])

def centroide(field_shape):
    """обчислюємо центроід поля.

    c = [[1,4,-5],[3,-2,9]] # of the form [[x1,x2,x3],[y1,y2,y3]]
    centroide = (sum(c[0])/len(c[0]),sum(c[1])/len(c[1]))
    повертаємо список [lattitude, longitude]
    """
    lat = []
    lon = []
    for dot in field_shape:
        lat.append(dot[1])
        lon.append(dot[0])
    lattitude = sum(lat)/len(lat)
    longitude = sum(lon)/len(lon)
    return [lattitude, longitude]

def posting(start_date, field_id, chemical_id):
    """повертаємо повідомлення про заплановане обприскування.
    
    вказуємо дату, тип і назву препарата, даємо посилання
    на карту з позначеним полем
    повертаємо список із строки повідомлення і списка [lattitude, longitude]
    """
    for chemical in chemicals:
        if chemical['id'] == chemical_id:
            chemical_name = chemical['name']
            chemical_type = chemical_types[chemical['chemical_type']]
            break
    for field in fields:
        if field['id'] == field_id:
            field_name = field['name']
            field_shape = json.loads(field['shape_simplified_geojson'])['coordinates'][0][0]
            field_locality = f", місце розташування: {field['locality']}" if field['locality'] else ''
            break
    return ['''На {0} планується обробка поля \"{1}\"{2}. Препарат: {3}, що входить до групи {4}.'''.format(start_date, field_name, field_locality, chemical_name, chemical_type), centroide(field_shape)]
# todo: замість дати підставляти слова "сбогодні/завтра/післязавтра"

def post_message(args:list):
    """відправляємо повідомлення в Телегу з API.
    
    надсилаємо текстове повідомлення і координати поля
    """
    message_params = {
     'chat_id': '333720683',  # ! потім замінити на id групи, в яку будемо постити
     'text': args[0]
    }
    location_params = {
    'chat_id': '333720683',  # ! потім замінити на id групи, в яку будемо постити
     'latitude': str(args[1][0]),
     'longitude': str(args[1][1]),
     'disable_notification': 'True'
    }
    response = requests.get(urls['BotMessage'], params=message_params)
    print(response.json())
    response = requests.get(urls['BotLocation'], params=location_params)
    print(response.json())
    return


if __name__ == '__main__':
    for operation in get_planned_operations(honey_fields_ids(honey_crops_ids())):
        post_message(posting(*operation))
