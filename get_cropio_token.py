from main import Cropwise

email = input("Give me e-mail: ")
password = input("Give me password: ")

print(Cropwise.get_cropio_token(email, password))
