import time
import smtplib
import requests
# Gmail account info
from credentials import gmail_user, gmail_password, to

# Replace with the path to your log file
log_file = '/home/pi/github/Get_Vigor165_DSL_Status/Get_Vigor165_DSL_Status.log'

last_line = ""

nutzern = ["1286415286", "1424553498"]


def send_telegram_message(message):
    try:
        for a in nutzern:
            requests.post(f'https://api.telegram.org/bot6035244747:AAHARS15swk47D-zcpFfSNb3DVzNQd-Tp_c/sendMessage?chat_id={a}&text={message}')
            print(f'Telegram message sent to {a}!')
    except Exception as e:
        print("Something went wrong while sending the Telegram message:", e)

while True:
    with open(log_file, "r") as f:
        lines = f.readlines()
        if lines[-1] != last_line:
            last_line = lines[-1]
            if "Entering showtime status" in last_line:
                message = "Subject: New showtime status\n\n" + "".join(lines[-6:])
                try:
                    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                    server.ehlo()
                    server.login(gmail_user, gmail_password)
                    server.sendmail(gmail_user, to, message)
                    server.close()
                    print('Email sent!')
                    send_telegram_message(message)
                except Exception as e:
                    print('Something went wrong...', e)
        f.close()
    time.sleep(60)

