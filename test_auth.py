import requests
import json

BMC_IP = "127.0.0.1"
BMC_PORT = "2443"
USERNAME = "root"
PASSWORD = "0penBmc"


def test_login_to_bmc():
    url = f"https://{BMC_IP}:{BMC_PORT}/redfish/v1/SessionService/Sessions"

    login_data = {"UserName": USERNAME, "Password": PASSWORD}

    headers = {"Content-Type": "application/json"}

    print("Отправляю запрос на вход...")
    response = requests.post(
        url=url, json=login_data, headers=headers, verify=False, timeout=10
    )

    print(f"Статус ответа: {response.status_code}")

    if response.status_code == 201:
        print("Вход успешен!")
        print(f"URL: {url}")

        auth_token = response.headers.get("X-Auth-Token")
        print(f"Получен токен: {auth_token}")

        session_info = response.json()
        print(f"Имя пользователя: {session_info.get('UserName')}")
        print(f"ID сессии: {session_info.get('Id')}")

        return True
    else:
        print(f"Ошибка входа! Код: {response.status_code}")
        print(f"URL: {url}")
        print(f"Ответ сервера: {response.text}")
        return False


if __name__ == "__main__":
    print("Запускаю тест аутентификации OpenBMC...")
    success = test_login_to_bmc()
