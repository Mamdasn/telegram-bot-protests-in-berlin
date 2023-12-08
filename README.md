# telegram-bot-protests-in-berlin
This telegram bot facilitates access to the protests registered in Berlin on berlin.de. Users can access protests based on their distinguishing features, such as location, date, theme, and route.

You can find an instance of this bot on telegram here: [@ProtestsBerlinBot:](https://t.me/ProtestsBerlinBot)

## Usage
First you should have access to a VPS. You can order it for cheap online. Make sure to export the environmental variables `IP_ADDRESS` and `TG_BOT_TOKEN`. Then, to set up and run the bot, start by running the command `docker compose up --build -d`.
To run the Telegram bot container, make sure you have already installed docker and docker-compose on your device. There you go, now you should have a fully functional Telegram bot running in a docker container.

| PORT | USAGE |
|------|-------|
| 443  | Establish a connection with telegram server |
| 9051 | Send a request to tor control for a new ip |

IP rotation can be automated using crontab (in this case every 24 hours):  
`0 */24 * * * echo -e 'AUTHENTICATE ""\r\nsignal NEWNYM\r\nQUIT' | nc localhost 9051`

## Documentation
The documentation can be found here: [Docs](https://mamdasn.github.io/telegram-bot-protests-in-berlin/)
