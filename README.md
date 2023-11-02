# telegram-bot-protests-in-berlin
This telegram bot facilitates access to the protests registered in Berlin on berlin.de. Users can access protests based on their distinguishing features, such as location, date, theme, and route.

## Usage
[@ProtestsBerlinBot:](https://t.me/ProtestsBerlinBot)

First you should have access to a VPS. You can order it for cheap online. Make sure to export the environmental variables `IP_ADDRESS` and `TG_BOT_TOKEN`. Then, to set up and run the bot, start by running the command `docker compose up --build -d`.
To run the Telegram bot container, make sure you have already installed docker and docker-compose on your device. There you go, now you should have a fully functional Telegram bot running in a docker container.
