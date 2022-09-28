"""Тренуюсь працювати з API взагалі та з API Cropio особисто.

спробуємо побудувати Телеграм-бота, що попереджатиме місцевих
пасічників про майбутні обприскування полів з медоносами
"""
import json
import time  # fixme спробувати замінити бібліотеку arrow на time
import logging
import logging.config
import os
import requests
from dotenv import load_dotenv
import yaml
import arrow

load_dotenv()
with open("logger.yaml", "r", encoding="utf-8") as logger_settings_file:
    logger_settings = yaml.load(logger_settings_file, yaml.Loader)
logging.config.dictConfig(logger_settings)
logger = logging.getLogger("app")

urls = {
    "BotMessage": f'https://api.telegram.org/bot{os.getenv("TOKEN_TELEGRAM")}/sendMessage',
    "BotLocation": f'https://api.telegram.org/bot{os.getenv("TOKEN_TELEGRAM")}/sendLocation',
}


class Cropwise:
    """Містить всі функції для роботи з API Cropwise."""
    def __init__(self, cropio_token) -> None:
        self.headers = {"Content-Type": "application/json"}
        self.headers["X-User-Api-Token"] = cropio_token  # os.getenv('TOKEN_CROPIO')
        self.now = time.localtime()
        while self.get_cropwise_info() - {200, 201, 204}:
            time.sleep(900)  # fixme додати обробку кількох невдалих запитів поспіль

    def get_cropwise_info(self):
        """отримуємо всю необхідну інформацію від Cropwise Operations.

        Returns:
            set: коди статусу відповідей від сервера
        """
        response_status = set()
        try:
            self.chemicals = requests.get(
                "https://operations.cropwise.com/api/v3/chemicals", headers=self.headers
            )  # забрали список наявних хімікатів, потім згодиться.
            response_status.add(self.chemicals.status_code)
            self.fields = requests.get(
                "https://operations.cropwise.com/api/v3/fields", headers=self.headers
            )  # і список полів.
            response_status.add(self.fields.status_code)
            self.crops = requests.get(
                "https://operations.cropwise.com/api/v3/crops", headers=self.headers
            )  # узнаємо які культури зареєстровано в системі
            response_status.add(self.crops.status_code)
            self.fieldses = requests.get(
                f"https://operations.cropwise.com/api/v3/history_items&year={self.now.tm_year}",
                headers=self.headers,
            )  # тут у нас всі поля
            response_status.add(self.fieldses.status_code)
            self.operations = requests.get(
                "https://operations.cropwise.com/api/v3/agro_operations",
                headers=self.headers,
            )  # а туточки - всі операції (заплановані, виконані, відмінені)
            response_status.add(self.operations.status_code)
        except Exception as excepty:
            logger.error("Помилка під час запиту до API Cropio: %s", excepty)
            response_status.add("exception")
        logger.info("Код статуса запита до API Cropio: %s", response_status)
        return response_status

    def honey_crops_ids(self):
        """отримуємо список з id медоносів.

        Returns:
            list: список з id  рослин, які є медоносами
        """
        crops_standard_name = {
            "buckwheat",
            "linum",
            "medicago",
            "oil_seed_raps_spring",
            "oil_seed_raps_winter",
            "sainfoin",
            "sunflower",
        }
        honey_crops_id = []
        for crop in self.crops.json()["data"]:
            if crop["standard_name"] in crops_standard_name:
                honey_crops_id.append(crop["id"])
        return honey_crops_id

    def honey_fields_ids(self, honey_crops):
        """отримуємо список id полів у поточному році з медоносами.

        Args:
            honey_crops (list): список з id медоносів, за яким відфільтровуватимуться поля в
            поточному році

        Returns:
            list: список з id полів
        """
        honey_fields_id = []
        for field in self.fieldses.json()["data"]:
            if (field["crop_id"] in honey_crops):
                honey_fields_id.append(field["field_id"])
        return honey_fields_id

    def get_planned_operations(self, honey_fields):
        """отримуємо список запланованих оприскувань.

        хімікатами на полях з медоносами на майбутнє або сьогодні,
        повертаємо ітератор
        """
        for operation in self.operations.json()["data"]:
            if (
                arrow.utcnow().floor("day")
                <= arrow.get(operation["planned_start_date"], "YYYY-MM-DD")
                <= arrow.utcnow().shift(days=+2).floor("day")
                and operation["field_id"] in honey_fields
                and operation["operation_subtype"] == "spraying"
                and operation["status"] == "planned"
            ):
                for item in operation["application_mix_items"]:
                    if item["applicable_type"] == "Chemical":
                        yield (
                            arrow.get(operation["planned_start_date"], "YYYY-MM-DD"),
                            operation["field_id"],
                            item["applicable_id"],
                        )

    def centroide(self, field_shape):
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
        lattitude = sum(lat) / len(lat)
        longitude = sum(lon) / len(lon)
        return [lattitude, longitude]

    def get_message(self, start_date, field_id, chemical_id):
        """повертаємо повідомлення про заплановане обприскування.

        вказуємо дату, тип і назву препарата, даємо посилання
        на карту з позначеним полем
        повертаємо список із строки повідомлення і списка [lattitude, longitude]
        """
        chemical_types = {
            "herbicide": "гербіциди",
            "insecticide": "інсектіциди",
            "fungicide": "фунгіциди",
            "growth_regulator": "регулятори росту",
            "seed_treatment": "протруйники",
            "other": "інше",
        }
        for chemical in self.chemicals.json()["data"]:
            if chemical["id"] == chemical_id:
                chemical_name = chemical["name"]
                chemical_type = chemical_types[chemical["chemical_type"]]
                break
        for field in self.fields.json()["data"]:
            if field["id"] == field_id:
                field_name = field["name"]
                field_shape = json.loads(field["shape_simplified_geojson"])[
                    "coordinates"
                ][0][0]
                field_locality = (
                    f", місце розташування: {field['locality']}"
                    if field["locality"]
                    else ""
                )
                break
        if start_date == arrow.utcnow():
            start_date_text = "сьогодні"
        elif start_date == arrow.utcnow().shift(days=+1):
            start_date_text = "завтра"
        else:
            start_date_text = "післязавтра"

        return [
            f'На {start_date_text} планується обробка поля "{field_name}"{field_locality}. Препарат: {chemical_name}, що входить до групи {chemical_type}.',
            self.centroide(field_shape),
        ]

    def get_cropio_token(self, email: str, password: str):
        """Отримуємо токен заючи e-mail і пароль."""
        values = json.dumps({"user_login": {"email": email, "password": password}})
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(
                "https://operations.cropwise.com/api/v3/sign_in",
                data=values,
                headers=headers,
            )
        except Exception as excepty:
            logger.error("Помилка під час запиту до API Cropio: %s", excepty)
        return response.json()["user_api_token"]


def post_message(args: list):
    """відправляємо повідомлення в Телегу з API."""
    message_params = {"chat_id": os.getenv("CHAT_ID"), "text": args[0]}
    location_params = {
        "chat_id": os.getenv("CHAT_ID"),
        "latitude": str(args[1][0]),
        "longitude": str(args[1][1]),
        "disable_notification": "True",
    }
    response = requests.get(
        urls["BotMessage"], params=message_params
    )  # надсилаємо текстове повідомлення
    print(response.json())
    response = requests.get(
        urls["BotLocation"], params=location_params
    )  # і координати поля
    print(response.json())
    return


if __name__ == "__main__":
    agrofirm = Cropwise(os.getenv("TOKEN_CROPIO"))
    for one_operation in agrofirm.get_planned_operations(
        agrofirm.honey_fields_ids(agrofirm.honey_crops_ids())
    ):
        post_message(agrofirm.get_message(*one_operation))
