import requests
import json

BMC_IP = "127.0.0.1"
BMC_PORT = "2443"


def test_get_system_info():
    print("1.Получаем токен доступа...")

    login_url = f"https://{BMC_IP}:{BMC_PORT}/redfish/v1/SessionService/Sessions"
    login_data = {"UserName": "root", "Password": "0penBmc"}

    headers = {"Content-Type": "application/json"}

    auth_response = requests.post(
        url=login_url,
        json=login_data,
        headers=headers,
        verify=False,
        timeout=10,
    )

    if auth_response.status_code != 201:
        print("Не удалось получить токен")
        return False

    auth_token = auth_response.headers.get("X-Auth-Token")

    print("\nОтправляем GET-запрос")

    system_url = f"https://{BMC_IP}:{BMC_PORT}/redfish/v1/Systems/system"

    headers = {"X-Auth-Token": auth_token, "Content-Type": "application/json"}

    response = requests.get(system_url, headers=headers, verify=False, timeout=10)

    print(f"Статус ответа: {response.status_code}")

    if response.status_code == 200:
        print("Статус-код 200 - запрос успешен")
    else:
        print(f"Ошибка! Ожидался статус 200, получен {response.status_code}")
        return False

    print("\nПроверяем наличие полей Status и PowerState в JSON")

    system_info = response.json()

    if "Status" in system_info:
        print("Поле 'Status' присутствует в ответе")
        status_info = system_info["Status"]
        print(f"Health: {status_info.get('Health', 'Unknown')}")
        print(f"State: {status_info.get('State', 'Unknown')}")
    else:
        print("Поле 'Status' отсутствует в ответе")
        return False

    if "PowerState" in system_info:
        print("Поле 'PowerState' присутствует в ответе")
        print(f"PowerState: {system_info['PowerState']}")
    else:
        print("Поле 'PowerState' отсутствует в ответе")
        return False

    return True


if __name__ == "__main__":
    print("Тест получения информации о системе")

    success = test_get_system_info()
