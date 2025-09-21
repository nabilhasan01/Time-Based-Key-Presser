import pydirectinput
import time
from datetime import datetime, timedelta

def press_f():
    pydirectinput.press('f')
    print(f"F pressed at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")

# Ask user for target time
target_time_input = input("Enter target time (HH:MM:SS): ")
now = datetime.now()
h, m, s = map(int, target_time_input.split(":"))

# Build today's target time
target_time = now.replace(hour=h, minute=m, second=s, microsecond=0)

# If time already passed today, schedule for tomorrow
if target_time < now:
    target_time += timedelta(days=1)

# Loop 10 times
for i in range(10):
    print(f"Waiting until {target_time.strftime('%H:%M:%S')} to press F...")

    # Busy-wait until target time
    while datetime.now() < target_time:
        time.sleep(0.05)

    press_f()
    target_time += timedelta(minutes=1)
