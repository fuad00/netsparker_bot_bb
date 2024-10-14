import ctypes
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
import time
import string
from urllib.parse import urlparse

# Путь к интерпретатору Python
python_executable = sys.executable

# Проверка запуска с правами администратора
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Функция для перезапуска скрипта с правами администратора
def run_as_admin():
    if not is_admin():
        try:
            params = " ".join([f'"{arg}"' for arg in sys.argv])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", python_executable, params, None, 1)
            return False  # Вернем False, чтобы завершить выполнение основного потока без выхода
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить с правами администратора: {e}")
            return False
    return True

# Проверяем, нужно ли перезапустить с правами администратора
if not run_as_admin():
    sys.exit()

# Функция для очистки доменного имени для использования в качестве имени файла
def sanitize_filename(name):
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
    sanitized = ''.join(c for c in name if c in valid_chars)
    return sanitized.replace(' ', '_')

# Функция для выбора файла доменов или ввода одного домена
def choose_file_or_domain():
    if var_input_type.get() == "file":
        filepath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if filepath:
            entry_domains.delete(0, tk.END)
            entry_domains.insert(0, filepath)
    else:
        entry_domains.delete(0, tk.END)
        entry_domains.insert(0, "")

# Функция для получения доменов
def get_domains():
    domains_input = entry_domains.get()
    if not domains_input:
        messagebox.showerror("Ошибка", "Пожалуйста, введите домен или выберите файл с доменами.")
        return None, None
    if os.path.isfile(domains_input):
        try:
            with open(domains_input, 'r', encoding='utf-8') as f:
                domains = [line.strip() for line in f.readlines() if line.strip()]
            return domains, domains_input  # Возвращаем список доменов и путь к файлу
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать файл доменов: {e}")
            return None, None
    else:
        return [domains_input.strip()], None  # Возвращаем список с одним доменом и None

# Функция для получения прокси
def get_proxy():
    selected_proxy = proxy_var.get()
    if selected_proxy == "custom":
        custom_proxy = entry_custom_proxy.get().strip()
        if not custom_proxy:
            messagebox.showerror("Ошибка", "Пожалуйста, введите адрес собственного прокси.")
            return None
        return custom_proxy
    return selected_proxy

# Функция для выбора исполняемого файла программы
def choose_executable(entry_field):
    filepath = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe"), ("Python files", "*.py"), ("All files", "*.*")])
    if filepath:
        entry_field.delete(0, tk.END)
        entry_field.insert(0, filepath)

# Фильтрация URL с параметрами для x8
def filter_urls_with_parameters(input_file, output_file):
    try:
        seen_urls = set()
        with open(input_file, 'r', encoding='utf-8') as infile:
            for line in infile:
                url = line.strip()
                if '?' in url or '&' in url:  # Проверка на наличие параметров
                    parsed_url = urlparse(url)
                    # Убираем фрагменты (если есть)
                    cleaned_url = parsed_url._replace(fragment='').geturl()
                    if cleaned_url not in seen_urls:
                        seen_urls.add(cleaned_url)
        with open(output_file, 'w', encoding='utf-8') as outfile:
            for url in seen_urls:
                outfile.write(url + '\n')
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при фильтрации URL: {e}")

# Функция для запуска внешних инструментов с правами администратора
def run_external_tool(command, success_message, error_message, progress_label):
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        print(stdout)
        print(stderr)
        if process.returncode == 0:
            progress_label.config(text=success_message)
        else:
            progress_label.config(text=error_message)
            messagebox.showerror("Ошибка", stderr)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Неожиданная ошибка: {e}")
        progress_label.config(text=error_message)

# Функция для запуска Katana
def run_katana(progress_label):
    katana_path = entry_katana_path.get().strip()
    if not os.path.exists(katana_path):
        messagebox.showerror("Ошибка", "Путь к Katana некорректен!")
        return

    domains, domains_input = get_domains()
    if not domains:
        return

    proxy = get_proxy()
    if not proxy:
        return

    threads = entry_threads.get() or "10"
    katana_args = entry_katana_args.get().strip()

    katana_output_file = "katana_output.txt"

    if domains_input and os.path.isfile(domains_input):
        # Если выбран файл с доменами, передаем его напрямую
        command = [katana_path, "-list", domains_input, "--proxy", proxy, "-c", threads, "-o", katana_output_file]
    else:
        # Иначе создаем временный файл с доменами
        with open("temp_domains.txt", "w", encoding='utf-8') as temp_file:
            for domain in domains:
                temp_file.write(domain + "\n")
        command = [katana_path, "-list", "temp_domains.txt", "--proxy", proxy, "-c", threads, "-o", katana_output_file]

    if katana_args:
        command.extend(katana_args.split())

    progress_label.config(text=f"Katana выполняется...")
    run_external_tool(command, "Katana завершила работу!", "Ошибка при запуске Katana", progress_label)

    # Удаляем временный файл, если он был создан
    if os.path.exists("temp_domains.txt"):
        os.remove("temp_domains.txt")

# Функция для запуска GoSpider
def run_gospider(progress_label):
    gospider_path = entry_gospider_path.get().strip()
    if not os.path.exists(gospider_path):
        messagebox.showerror("Ошибка", "Путь к GoSpider некорректен!")
        return

    domains, domains_input = get_domains()
    if not domains:
        return

    proxy = get_proxy()
    if not proxy:
        return

    threads = entry_threads.get() or "10"
    gospider_args = entry_gospider_args.get().strip()

    gospider_output_file = "gospider_output_data.txt"  # Изменено имя файла

    if domains_input and os.path.isfile(domains_input):
        command = [gospider_path, "-S", domains_input, "--proxy", proxy, "-c", threads, "-t", threads]
    else:
        with open("temp_domains.txt", "w", encoding='utf-8') as temp_file:
            for domain in domains:
                temp_file.write(domain + "\n")
        command = [gospider_path, "-S", "temp_domains.txt", "--proxy", proxy, "-c", threads, "-t", threads]

    if gospider_args:
        command.extend(gospider_args.split())

    progress_label.config(text=f"GoSpider выполняется...")

    # Запускаем процесс и захватываем вывод
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()

    if process.returncode == 0:
        print(stdout)
        print(f"GoSpider завершила работу.")
        progress_label.config(text="GoSpider завершила работу!")
        # Записываем stdout в файл
        try:
            with open(gospider_output_file, 'w', encoding='utf-8') as f:
                f.write(stdout)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось записать в файл {gospider_output_file}: {e}")
            return
    else:
        print(stderr)
        progress_label.config(text="Ошибка при запуске GoSpider")
        messagebox.showerror("Ошибка", f"Ошибка при запуске GoSpider: {stderr}")

    if os.path.exists("temp_domains.txt"):
        os.remove("temp_domains.txt")

# Функция для запуска xnLinkFinder
def run_xnlinkfinder(progress_label):
    xnlinkfinder_path = entry_xnlinkfinder_path.get().strip()
    if not os.path.exists(xnlinkfinder_path):
        messagebox.showerror("Ошибка", "Путь к xnLinkFinder некорректен!")
        return

    domains, domains_input = get_domains()
    if not domains:
        return

    proxy = get_proxy()
    if not proxy:
        return

    xnlinkfinder_args = entry_xnlinkfinder_args.get().strip()

    combined_output_file = "combined_output.txt"
    xnlinkfinder_output_file = "xnlinkfinder_output.txt"

    # Объединяем файлы Katana и GoSpider
    try:
        # Wait before reading gospider_output_data.txt to ensure GoSpider has released the file
        time.sleep(1)
        with open(combined_output_file, "w", encoding='utf-8') as combined_file:
            katana_output_file = "katana_output.txt"
            gospider_output_file = "gospider_output_data.txt"  # Используем новое имя файла
            if os.path.exists(katana_output_file):
                with open(katana_output_file, "r", encoding='utf-8') as katana_file:
                    combined_file.write(katana_file.read())
            if os.path.exists(gospider_output_file):
                with open(gospider_output_file, "r", encoding='utf-8') as gospider_file:
                    combined_file.write(gospider_file.read())
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при объединении файлов: {e}")
        return

    # Проверяем, что параметр -sf задан
    if "-sf" not in xnlinkfinder_args:
        # Записываем домены в файл
        with open("scope_filter.txt", "w", encoding='utf-8') as sf_file:
            for domain in domains:
                netloc = urlparse(domain).netloc or domain
                sf_file.write(netloc + "\n")
        xnlinkfinder_args += f" -sf scope_filter.txt"

    # Проверяем, что параметр -d задан
    if "-d" not in xnlinkfinder_args and "--depth" not in xnlinkfinder_args:
        xnlinkfinder_args += " -d 2"

    command = [python_executable, xnlinkfinder_path, "-i", combined_output_file, "-o", xnlinkfinder_output_file, "-rp", proxy]
    if xnlinkfinder_args:
        command.extend(xnlinkfinder_args.split())

    progress_label.config(text=f"xnLinkFinder выполняется...")
    run_external_tool(command, "xnLinkFinder завершила работу!", "Ошибка при запуске xnLinkFinder", progress_label)

    # Удаляем файл scope_filter.txt
    if os.path.exists("scope_filter.txt"):
        os.remove("scope_filter.txt")

    # Фильтрация URL для x8
    filtered_links_file = "filtered_links_for_x8.txt"
    filter_urls_with_parameters(xnlinkfinder_output_file, filtered_links_file)
    if var_x8.get() == 1:
        run_x8(filtered_links_file, proxy, progress_label)

# Функция для запуска x8
def run_x8(filtered_links_file, proxy, progress_label):
    x8_path = entry_x8_path.get().strip()
    if not os.path.exists(x8_path):
        messagebox.showerror("Ошибка", "Путь к x8 некорректен!")
        return

    medium_path = entry_medium_path.get().strip()  # Wordlist file path
    if not os.path.exists(medium_path):
        messagebox.showerror("Ошибка", "Путь к medium.txt некорректен!")
        return

    workers = entry_workers.get() or "100"  # Устанавливаем 100 воркеров по умолчанию
    threads = entry_threads.get() or "10"  # Default thread count
    x8_args = entry_x8_args.get().strip()  # Any additional user-provided arguments

    x8_output_file = "x8_output.txt"  # File to store output

    # Удаляем дубликаты из файла перед запуском x8
    unique_urls = set()
    with open(filtered_links_file, 'r', encoding='utf-8') as infile:
        for line in infile:
            unique_urls.add(line.strip())
    with open(filtered_links_file, 'w', encoding='utf-8') as outfile:
        for url in unique_urls:
            outfile.write(url + '\n')

    # Building the command for x8
    command = [
        x8_path,
        "-u", filtered_links_file,  # Use -u to specify the file with URLs
        "-o", x8_output_file,  # Output file
        "-w", medium_path,  # Wordlist file
        "-c", threads,  # Concurrency control
        "-W", workers  # Worker control
    ]

    if x8_args:
        command.extend(x8_args.split())  # Append any additional arguments

    # Добавляем --replay-proxy с прокси
    if proxy:
        command.extend(["--replay-proxy", proxy])

    progress_label.config(text="x8 выполняется...")
    print(f"Запуск x8 с командой: {' '.join(command)}")  # For debugging purposes
    run_external_tool(command, "x8 успешно завершила работу!", "Ошибка при запуске x8", progress_label)

# Функция для запуска всех программ в отдельном потоке
def run_all():
    # Отключаем кнопку запуска, чтобы избежать повторных запусков
    btn_run_all.config(state=tk.DISABLED)
    # Создаем поток для выполнения задач
    threading.Thread(target=run_all_tasks).start()

def run_all_tasks():
    try:
        progress_label.config(text="Начало работы Katana...")
        run_katana(progress_label)
        progress_label.config(text="Начало работы GoSpider...")
        run_gospider(progress_label)
        progress_label.config(text="Начало работы xnLinkFinder...")
        run_xnlinkfinder(progress_label)
        progress_label.config(text="Все задачи выполнены!")
    finally:
        # Восстанавливаем состояние кнопки запуска
        btn_run_all.config(state=tk.NORMAL)

# Создание GUI
root = tk.Tk()
root.title("Запуск Katana, GoSpider, xnLinkFinder и x8")
root.geometry("800x750")
root.configure(bg="white")

# Создаем вкладки
notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

# Вкладка "Общие настройки"
frame_general = tk.Frame(notebook, bg="white")
notebook.add(frame_general, text="Общие настройки")

# Ввод домена или выбор файла
var_input_type = tk.StringVar(value="single")
tk.Radiobutton(frame_general, text="Один домен", variable=var_input_type, value="single", bg="white", command=choose_file_or_domain).pack(anchor='w', pady=5)
tk.Radiobutton(frame_general, text="Файл с доменами", variable=var_input_type, value="file", bg="white", command=choose_file_or_domain).pack(anchor='w', pady=5)

entry_domains = tk.Entry(frame_general, width=70)
entry_domains.pack(pady=5)

# Выбор прокси
proxy_var = tk.StringVar(value="http://127.0.0.1:8080")
tk.Label(frame_general, text="Выберите прокси", bg="white").pack(pady=5)
tk.Radiobutton(frame_general, text="http://127.0.0.1:8080", variable=proxy_var, value="http://127.0.0.1:8080", bg="white").pack(anchor='w')
tk.Radiobutton(frame_general, text="http://127.0.0.1:10010", variable=proxy_var, value="http://127.0.0.1:10010", bg="white").pack(anchor='w')
tk.Radiobutton(frame_general, text="Свой прокси", variable=proxy_var, value="custom", bg="white").pack(anchor='w')
entry_custom_proxy = tk.Entry(frame_general, width=70)
entry_custom_proxy.pack(pady=5)

# Количество потоков
tk.Label(frame_general, text="Количество потоков", bg="white").pack(pady=5)
entry_threads = tk.Entry(frame_general, width=70)
entry_threads.pack(pady=5)
entry_threads.insert(0, "10")  # Дефолтное значение

# Вкладка "Katana"
frame_katana = tk.Frame(notebook, bg="white")
notebook.add(frame_katana, text="Katana")

tk.Label(frame_katana, text="Путь к Katana", bg="white").pack(pady=5)
entry_katana_path = tk.Entry(frame_katana, width=70)
entry_katana_path.insert(0, r"C:\Users\kssmu\OneDrive\katana.exe")
entry_katana_path.pack(pady=5)
btn_choose_katana = tk.Button(frame_katana, text="Выбрать Katana", command=lambda: choose_executable(entry_katana_path))
btn_choose_katana.pack(pady=5)

tk.Label(frame_katana, text="Дополнительные аргументы для Katana", bg="white").pack(pady=5)
entry_katana_args = tk.Entry(frame_katana, width=70)
entry_katana_args.pack(pady=5)
entry_katana_args.insert(0, "-hl -aff -fx -jsl -d 15 -kf all -tls-impersonate -s breadth-first -rl 500 --timeout 50 -j")

# Вкладка "GoSpider"
frame_gospider = tk.Frame(notebook, bg="white")
notebook.add(frame_gospider, text="GoSpider")

tk.Label(frame_gospider, text="Путь к GoSpider", bg="white").pack(pady=5)
entry_gospider_path = tk.Entry(frame_gospider, width=70)
entry_gospider_path.insert(0, r"C:\Users\kssmu\OneDrive\gospider.exe")
entry_gospider_path.pack(pady=5)
btn_choose_gospider = tk.Button(frame_gospider, text="Выбрать GoSpider", command=lambda: choose_executable(entry_gospider_path))
btn_choose_gospider.pack(pady=5)

tk.Label(frame_gospider, text="Дополнительные аргументы для GoSpider", bg="white").pack(pady=5)
entry_gospider_args = tk.Entry(frame_gospider, width=70)
entry_gospider_args.pack(pady=5)
entry_gospider_args.insert(0, "--depth 0 --other-source --robots -a --timeout 50 -w")

# Вкладка "xnLinkFinder"
frame_xnlinkfinder = tk.Frame(notebook, bg="white")
notebook.add(frame_xnlinkfinder, text="xnLinkFinder")

tk.Label(frame_xnlinkfinder, text="Путь к xnLinkFinder", bg="white").pack(pady=5)
entry_xnlinkfinder_path = tk.Entry(frame_xnlinkfinder, width=70)
entry_xnlinkfinder_path.insert(0, r"C:\Users\kssmu\OneDrive\xnLinkFinder.py")
entry_xnlinkfinder_path.pack(pady=5)
btn_choose_xnlinkfinder = tk.Button(frame_xnlinkfinder, text="Выбрать xnLinkFinder", command=lambda: choose_executable(entry_xnlinkfinder_path))
btn_choose_xnlinkfinder.pack(pady=5)

tk.Label(frame_xnlinkfinder, text="Дополнительные аргументы для xnLinkFinder", bg="white").pack(pady=5)
entry_xnlinkfinder_args = tk.Entry(frame_xnlinkfinder, width=70)
entry_xnlinkfinder_args.pack(pady=5)
entry_xnlinkfinder_args.insert(0, "-d 2")

# Вкладка "x8"
frame_x8 = tk.Frame(notebook, bg="white")
notebook.add(frame_x8, text="x8")

tk.Label(frame_x8, text="Путь к x8", bg="white").pack(pady=5)
entry_x8_path = tk.Entry(frame_x8, width=70)
entry_x8_path.insert(0, r"C:\Users\kssmu\AppData\Local\Programs\Python\Python312\Scripts\x8.exe")
entry_x8_path.pack(pady=5)
btn_choose_x8 = tk.Button(frame_x8, text="Выбрать x8", command=lambda: choose_executable(entry_x8_path))
btn_choose_x8.pack(pady=5)

tk.Label(frame_x8, text="Путь к medium.txt (wordlist)", bg="white").pack(pady=5)
entry_medium_path = tk.Entry(frame_x8, width=70)
entry_medium_path.insert(0, r"C:\Users\kssmu\AppData\Local\Programs\Python\Python312\Scripts\medium.txt")
entry_medium_path.pack(pady=5)
btn_choose_medium = tk.Button(frame_x8, text="Выбрать medium.txt", command=lambda: choose_executable(entry_medium_path))
btn_choose_medium.pack(pady=5)

tk.Label(frame_x8, text="Количество воркеров для x8", bg="white").pack(pady=5)
entry_workers = tk.Entry(frame_x8, width=70)
entry_workers.pack(pady=5)
entry_workers.insert(0, "100")  # Устанавливаем 100 воркеров

tk.Label(frame_x8, text="Дополнительные аргументы для x8", bg="white").pack(pady=5)
entry_x8_args = tk.Entry(frame_x8, width=70)
entry_x8_args.pack(pady=5)
entry_x8_args.insert(0, "-X POST GET --encode --mimic-browser --remove-empty")

# Чекбокс для включения x8
var_x8 = tk.IntVar(value=1)
chk_x8 = tk.Checkbutton(frame_x8, text="Включить x8 после xnLinkFinder", variable=var_x8, bg="white")
chk_x8.pack(pady=10)

# Индикатор прогресса
progress_label = tk.Label(root, text="Готово.", bg="white", font=('Helvetica', 12))
progress_label.pack(pady=10)

# Кнопка запуска
btn_run_all = tk.Button(root, text="Запустить все", command=run_all, bg="green", fg="white", font=('Helvetica', 12, 'bold'))
btn_run_all.pack(pady=10)

root.mainloop()
