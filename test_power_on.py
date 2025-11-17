import requests
import json
import time

BMC_IP = "127.0.0.1"
BMC_PORT = "2443"


def test_power_on():
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
    token = auth_response.headers.get("X-Auth-Token")

    headers = {"X-Auth-Token": token, "Content-Type": "application/json"}

    print("\nПроверяем текущее состояние сервера...")
    system_url = f"https://{BMC_IP}:{BMC_PORT}/redfish/v1/Systems/system"
    response = requests.get(system_url, headers=headers, verify=False)

    if response.status_code == 200:
        system_info = response.json()
        current_power = system_info.get("PowerState", "Unknown")
        print(f"Текущее состояние питания: {current_power}")

    print("\nОтправляем команду ВКЛЮЧЕНИЯ...")
    power_on_url = f"https://{BMC_IP}:{BMC_PORT}/redfish/v1/Systems/system"
    power_on_data = {"ResetType": "On"}

    print(f"Отправляем POST запрос")
    print(f"Данные: {json.dumps(power_on_data)}")

    power_response = requests.post(
        power_on_url, json=power_on_data, headers=headers, verify=False, timeout=10
    )

    print(f"Статус ответа: {power_response.status_code}")

    if power_response.status_code == 204:
        print("202 Accepted - команда принята в обработку!")
    else:
        print(f"Ошибка! Ожидался статус 202, получен {power_response.status_code}")
        return False

    response = requests.get(system_url, headers=headers, verify=False)

    if response.status_code == 200:
        system_info = response.json()
        new_power = system_info.get("PowerState", "Unknown")
        print(f"Новое состояние питания: {new_power}")

        if new_power == "On":
            print("PowerState изменился на 'On' - сервер ВКЛЮЧЕН!")
            return True
        else:
            print(f"PowerState не изменился на 'On'. Текущее: {new_power}")
            return False
    else:
        print(f"Не удалось получить новое состояние: {response.status_code}")
        return False


if __name__ == "__main__":
    print("ЗАПУСК ТЕСТА УПРАВЛЕНИЯ ПИТАНИЕМ")
    success = test_power_on()
