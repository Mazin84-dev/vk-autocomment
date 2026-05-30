import requests
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

CURRENCIES = {"USD": "Доллар США", "EUR": "Евро", "GBP": "Фунт стерлингов"}

def fetch_rates(dt: date) -> dict:
    url = f"https://www.cbr.ru/scripts/XML_daily.asp?date_req={dt.strftime('%d/%m/%Y')}"
    resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    resp.encoding = "windows-1251"
    root = ET.fromstring(resp.text)
    result = {}
    for valute in root.findall("Valute"):
        code = valute.findtext("CharCode")
        if code in CURRENCIES:
            nominal = int(valute.findtext("Nominal"))
            value = float(valute.findtext("Value").replace(",", "."))
            result[code] = round(value / nominal, 4)
    return result

def get_workdays_may2026():
    days = []
    d = date(2026, 5, 1)
    while d.month == 5:
        if d.weekday() < 5:  # Пн-Пт
            days.append(d)
        d += timedelta(days=1)
    return days

def style_header(ws, row, col, value):
    cell = ws.cell(row=row, column=col, value=value)
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor="1F4E79")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    thin = Side(style="thin", color="FFFFFF")
    cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)
    return cell

def style_data(ws, row, col, value, is_date=False):
    cell = ws.cell(row=row, column=col, value=value)
    cell.alignment = Alignment(horizontal="center")
    fill_color = "D6E4F0" if row % 2 == 0 else "FFFFFF"
    cell.fill = PatternFill("solid", fgColor=fill_color)
    thin = Side(style="thin", color="CCCCCC")
    cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)
    if not is_date:
        cell.number_format = "#,##0.0000"
    else:
        cell.number_format = "DD.MM.YYYY"
    return cell

def main():
    days = get_workdays_may2026()
    print(f"Рабочих дней в мае 2026: {len(days)}")

    wb = Workbook()
    ws = wb.active
    ws.title = "Курсы ЦБ РФ май 2026"

    # Заголовки
    headers = ["Дата", "USD (руб.)", "EUR (руб.)", "GBP (руб.)"]
    for col, h in enumerate(headers, 1):
        style_header(ws, 1, col, h)

    ws.row_dimensions[1].height = 22
    ws.column_dimensions["A"].width = 14
    for col in ["B", "C", "D"]:
        ws.column_dimensions[col].width = 14

    all_rates = {}
    for i, dt in enumerate(days, 1):
        print(f"  {dt.strftime('%d.%m.%Y')} ...", end=" ", flush=True)
        try:
            rates = fetch_rates(dt)
            all_rates[dt] = rates
            row = i + 1
            style_data(ws, row, 1, dt, is_date=True)
            for j, code in enumerate(["USD", "EUR", "GBP"], 2):
                style_data(ws, row, j, rates.get(code))
            print("OK")
        except Exception as e:
            print(f"ОШИБКА: {e}")

    # Итоговый лист со статистикой
    ws2 = wb.create_sheet("Статистика")
    stats_headers = ["Валюта", "Мин (руб.)", "Макс (руб.)", "Среднее (руб.)"]
    for col, h in enumerate(stats_headers, 1):
        style_header(ws2, 1, col, h)
    for col in ["A", "B", "C", "D"]:
        ws2.column_dimensions[col].width = 16

    for row, code in enumerate(["USD", "EUR", "GBP"], 2):
        vals = [r[code] for r in all_rates.values() if code in r]
        if vals:
            ws2.cell(row=row, column=1, value=f"{code} — {CURRENCIES[code]}").font = Font(bold=True)
            ws2.cell(row=row, column=2, value=min(vals)).number_format = "#,##0.0000"
            ws2.cell(row=row, column=3, value=max(vals)).number_format = "#,##0.0000"
            ws2.cell(row=row, column=4, value=round(sum(vals)/len(vals), 4)).number_format = "#,##0.0000"

    fname = "cbr_rates_may2026.xlsx"
    wb.save(fname)
    print(f"\nФайл сохранён: {fname}")

if __name__ == "__main__":
    main()
