@echo off
call venv\Scripts\activate
set TOKEN_TELEGRAM=<put your token here>
set TOKEN_CROPIO=<put your token here>
set CHAT_ID=<and here - id of Telegram chat-group>
python main.py
pause