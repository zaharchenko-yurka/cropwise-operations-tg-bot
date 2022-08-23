import requests
import json

status_codes = {
    '200': 'OK — Запит був успішним',
    '201': 'Created — Запит був успішним, і був створений ресурс',
    '204': 'No Content — Запит був успішним, але немає представництва для повернення (тобто відповідь порожня)',
    '400': 'Bad Request — Запит не міг бути зрозумілим або відсутній потрібні параметри',
    '401': 'Unauthorized — Автентифікація не вдалась, або користувач не має дозволів на запитувану операцію',
    '403': 'Forbidden — Доступ заборонено',
    '404': 'Not Found — Ресурс не був знайдений',
    '422': 'Unprocessable Entity - Запит був добре сформованим, але його не вдалося дотримуватися через семантичні помилки',
    '503': 'Service Unavailable — Сервіс тимчасовий недоступний (наприклад, заплановане технічне обслуговування платформи). Спробуйте ще раз пізніше'
    }
urls = {
  'AgriWorkPlan': 'https://operations.cropwise.com/api/v3/agri_work_plans',
  'ApplicationMixItems': 'https://operations.cropwise.com/api/v3/application_mix_items',
  'AgroOperations': 'https://operations.cropwise.com/api/v3/agro_operations',
  'AgroOperations/v3a': 'https://operations.cropwise.com/api/v3a/agro_operations',
  'Crops': 'https://operations.cropwise.com/api/v3/crops',
  'Chemicals': 'https://operations.cropwise.com/api/v3/chemicals',
  'Fields': 'https://operations.cropwise.com/api/v3/fields',
  'Fields/v3a': 'https://operations.cropwise.com/api/v3a/fields',
  'HistoryItems': 'https://operations.cropwise.com/api/v3/history_items',
  'WeatherItem': 'https://operations.cropwise.com/api/v3/weather_items',
  'WorkType': 'https://operations.cropwise.com/api/v3/work_types',
  'WorkTypeAllowedCrops': 'https://operations.cropwise.com/api/v3/work-type-allowed-crops'
}

headers = {
  'Content-Type': 'application/json',
  'X-User-Api-Token': 'n3bR3d7WNNMEG9TXEdBZ'
}

# response = requests.get(urls['Fields'], headers = headers)
# print(response.status_code, status_codes[str(response.status_code)], sep=': ')
with open ("fields.txt", "r") as f:
#     f.write(str(response.text))
    dictionare = json.loads(json.load(f)['data'][0]['shape_simplified_geojson'])['coordinates'][0][0]
print(dictionare[5])