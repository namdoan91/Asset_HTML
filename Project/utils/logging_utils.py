import time

logs = []

def log_message(message):
    timestamp = time.strftime('%H:%M:%S')
    logs.append(f"{timestamp} - {message}")
    print(f"{timestamp} - {message}")