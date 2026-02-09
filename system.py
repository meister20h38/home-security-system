from ultralytics import YOLO
import gpiozero
import LCD1602
import time
import subprocess as sb
from email.message import EmailMessage
import smtplib
from dotenv import load_dotenv
import os

model = YOLO('best.pt')
sensor = gpiozero.DigitalInputDevice(pin=25, pull_up=False)

def take_picture():
    cmd = ['fswebcam', '-d', '/dev/video0', '-r', '640x480', '--no-banner', 'picture.jpg']
    sb.run(cmd)


def lcd(line1, line2):
    LCD1602.clear()
    LCD1602.write(0, 0, line1)
    LCD1602.write(0, 1, line2)


def detect_human():
    results = model.predict('picture.jpg', save=False, verbose=False)
    boxes = results[0].boxes

    if boxes is not None and hasattr(boxes, 'conf') and len(boxes.conf) > 0:
        for conf in boxes.conf:
            if conf.item() >= 0.6:
                return True
    return False


def detect_motion():
    return sensor.value == 1


def send_picture():
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT"))
    RECEIVER = os.getenv("RECEIVER")

    msg = EmailMessage()
    msg['Subject'] = '訪問者が現れました'
    msg['From'] = EMAIL_USER
    msg['To'] = RECEIVER
    msg.set_content('訪問者の画像を添付します')

    with open('picture.jpg', 'rb') as f:
        img_data = f.read()
    msg.add_attachment(img_data, maintype='image', subtype='jpeg', filename='visitor.jpg')

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)


def main():
	load_dotenv()
    	LCD1602.init(0x27, 1)

    	# --- 実行時間チェック ---
    	now = datetime.now()
    	# 18:00以降 または 9:00より前 の場合にのみ実行
    	if not (now.hour >= 18 or now.hour < 9):
        	print(f"Out of service hours ({now.strftime('%H:%M:%S')}). System will exit.")
        	lcd("Out of Service", f"Time: {now.strftime('%H:%M')}")
        	time.sleep(5)
        	LCD1602.clear()
        	sys.exit() # プログラムを終了

    	lcd("System Booted", "Starting watch...")
    	print("System started. Press Ctrl+C to exit.")
    	time.sleep(2)

    	try:
        	while True:
            	lcd("Watching...", "")
            	print("Watching for motion...")
            	sensor.wait_for_active()
            
            	print("Motion detected!")
            	lcd("Motion Detected!", "Taking Photo...")
            
            	take_picture()
            
            	lcd("Analyzing Image", "Please wait...")
            	if detect_human():
                	lcd("Human Detected!", "Sending Email...")
                
                	try:
                    		send_picture()
                    		lcd("Email Sent", "Successfully")
                    		print("Waiting for 15 seconds to prevent continuous emails.")
                    		time.sleep(15)
                	except Exception as e:
                    		print(f"Email sending failed: {e}")
                    		lcd("Email Failed", "Check logs.")
                    		time.sleep(5)
            	else:
                	lcd("No Human Found", "Resuming watch...")
                	time.sleep(3)

    	except KeyboardInterrupt:
        	print("\nProgram terminated by user.")
    	finally:
        	LCD1602.clear()
        	print("Cleanup complete. System shutdown.")


if __name__ == "__main__":
    main()
