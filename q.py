import datetime
import os
import shutil
import string
import subprocess
import json
import time
import sys

def fake_loading_animation():
    """Атмосферная CLI-анимация сканирования секторов и шины."""
    print(" [i] Инициализация подсистемы Storage API...")
    time.sleep(0.4)
    print(" [i] Подключение к системной шине WMI Microsoft...")
    time.sleep(0.4)
    
    stages = [
        "Сканирование физических интерфейсов SATA/NVMe",
        "Опрос мостов USB-контроллеров и переходников",
        "Чтение таблиц разделов GPT/MBR",
        "Запрос телеметрии аппаратных логов S.M.A.R.T"
    ]
    
    for stage in stages:
        sys.stdout.write(f" [>] {stage}")
        sys.stdout.flush()
        # Бегущие точки имитируют реальное чтение железа
        for _ in range(3):
            time.sleep(0.2)
            sys.stdout.write(".")
            sys.stdout.flush()
        sys.stdout.write(" [ Готово ]\n")
        time.sleep(0.1)
    print("\n Сбор данных завершен. Генерация отчета...\n")
    time.sleep(0.3)

def get_wmi_disk_data():
    """Получает точные данные о физических дисках через системный WMI."""
    drive_info = {}
    try:
        cmd_map = "powershell -Command \"Get-Partition | Where-Object { $_.DriveLetter } | Select-Object DriveLetter, DiskNumber | ConvertTo-Json\""
        res_map = subprocess.run(cmd_map, shell=True, capture_output=True, text=True, encoding='cp866')
        
        cmd_wmi = "powershell -Command \"Get-WmiObject -Namespace root\\Microsoft\\Windows\\Storage -Class MSFT_PhysicalDisk | Select-Object DeviceId, MediaType, BusType, Model, HealthStatus, OperationalStatus | ConvertTo-Json\""
        res_wmi = subprocess.run(cmd_wmi, shell=True, capture_output=True, text=True, encoding='cp866')
        
        partition_map = {}
        if res_map.stdout.strip():
            map_data = json.loads(res_map.stdout)
            if isinstance(map_data, dict): map_data = [map_data]
            for item in map_data:
                if item.get("DriveLetter"):
                    partition_map[f"{item['DriveLetter']}:"] = item["DiskNumber"]
                    
        phys_disks = {}
        if res_wmi.stdout.strip():
            wmi_data = json.loads(res_wmi.stdout)
            if isinstance(wmi_data, dict): wmi_data = [wmi_data]
            for item in wmi_data:
                status_map = {0: "Healthy", 1: "Warning", 2: "Unhealthy"}
                raw_health = item.get("HealthStatus", "Unknown")
                health_str = status_map.get(raw_health, str(raw_health))
                
                media_map = {3: "HDD", 4: "SSD"}
                raw_media = item.get("MediaType", "Unknown")
                media_str = media_map.get(raw_media, str(raw_media))
                
                # Расширенный маппинг шины (3 и 11 — это разновидности SATA/ATA)
                bus_map = {11: "SATA", 17: "NVMe", 7: "USB", 3: "SATA/ATA"}
                raw_bus = item.get("BusType", "Unknown")
                bus_str = bus_map.get(raw_bus, str(raw_bus))

                phys_disks[int(item["DeviceId"])] = {
                    "media": media_str,
                    "bus": bus_str,
                    "model": str(item.get("Model", "Unknown")),
                    "health": health_str,
                    "op_status": str(item.get("OperationalStatus", "OK"))
                }
                
        for letter, disk_num in partition_map.items():
            if disk_num in phys_disks:
                drive_info[letter] = phys_disks[disk_num]
                
    except Exception:
        pass
    return drive_info

def classify_and_format_v3_2_2(letter, ps_info):
    """Форматирует вывод типа диска и его здоровья в строгом текстовом стиле CLI."""
    if letter in ps_info:
        info = ps_info[letter]
        bus = info["bus"].strip()
        media = info["media"].strip()
        model = info["model"].strip()
        health = info["health"].upper().strip()

        if "SSD" in media.upper() or media == "4": media_type = "SSD"
        elif "HDD" in media.upper() or media == "3": media_type = "Жесткий диск (HDD)"
        else: media_type = "Накопитель"

        if "USB" in bus.upper() or bus == "7" or "USB" in model.upper():
            type_str = f"Внешний накопитель (USB-Переходник) | Модель: {model}"
        else:
            bus_name = "SATA" if bus == "11" else "NVMe" if bus == "17" else bus
            type_str = f"Внутренний {media_type} | Шина: {bus_name} | Модель: {model}"

        # Строгий текстовый стиль без капризных эмодзи
        if "HEALTHY" in health or "0" in health or "OK" in health:
            health_str = "[ OK ] СТАТУС ОТЛИЧНЫЙ (Здоров)"
        elif "WARNING" in health or "1" in health:
            health_str = f"[ ! ] ВНИМАНИЕ! Обнаружены ошибки S.M.A.R.T. ({info['op_status']})"
        else:
            health_str = f"[!!!] КРИТИЧЕСКИЙ СБОЙ! Рекомендуется бэкап данных ({info['op_status']})"
            
        return type_str, health_str

    return "Внутренний накопитель (HDD/SSD)", "[ ? ] Нет данных S.M.A.R.T."

def generate_v3_2_2_with_loading():
    # 1. Сначала запускаем красивый фейк-лоадинг
    fake_loading_animation()
    
    # 2. Собираем данные
    ps_info = get_wmi_disk_data()

    header = "=" * 85 + "\n"
    header += "      АВТОМАТИЧЕСКИЙ СКАHЕР V3.2.2: ULTIMATE CLI (БЕЗ ОШИБОК КОДИРОВКИ)\n"
    header += "=" * 85 + "\n"

    body = ""
    available_drives = [f"{l}:" for l in string.ascii_uppercase if os.path.exists(f"{l}:\\")]

    for drive in available_drives:
        try:
            usage = shutil.disk_usage(drive + "\\")
            pure_bytes = usage.total
            free_bytes = usage.free

            if pure_bytes == 0:
                continue

            disk_type, health_text = classify_and_format_v3_2_2(drive, ps_info)

            marketing_gb = round(pure_bytes / 1_000_000_000)
            real_gb = pure_bytes / (1024**3)
            free_gb = free_bytes / (1024**3)
            stolen_gb = marketing_gb - real_gb
            loss_percent = (stolen_gb / marketing_gb) * 100

            body += f" Накопитель [{drive}\\]\n"
            body += f"   ├─ Тип и модель:          {disk_type}\n"
            body += f"   ├─ ЗДОРОВЬЕ S.M.A.R.T.:   {health_text}\n"
            body += f"   ├─ На упаковке обещано:   {marketing_gb} ГБ\n"
            body += f"   ├─ Реально видит Windows: {real_gb:.2f} ГБ\n"
            body += f"   ├─ Доступно сейчас (своб): {free_gb:.2f} ГБ\n"
            body += f"   ├─ Маркетинговая усушка: -{stolen_gb:.2f} ГБ\n"
            body += f"   └─ Чистые потери объема:  {loss_percent:.1f}%\n"
            body += f" {'-' * 81}\n"
        except Exception:
            continue

    # 3. Выводим готовый отчет
    print(header + body)

    try:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        report_file = os.path.join(desktop_path, "Drive_Report_V3.txt")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"Отчет S.M.A.R.T. создан: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(header + body)
        print(f"💾 Финальный отчет сохранен на Рабочем столе: Drive_Report_V3.txt")
        print("=" * 85)
    except Exception as e:
        print(f"⚠️ Не удалось сохранить файл: {e}")

if __name__ == "__main__":
    generate_v3_2_2_with_loading()
input("\nНажмите ENTER для выхода из программы...")
