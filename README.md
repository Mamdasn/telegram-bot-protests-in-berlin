# telegram-bot-protests-in-berlin
The purpose of this code base is to facilitate access to the protests registered in Berlin on berlin.de. Users can access protests based on their distinguishing features, such as location, date, theme, and route.

[![Dockerhub Publish and Deploy on host](https://github.com/Mamdasn/telegram-bot-protests-in-berlin/actions/workflows/build-and-push-to-dockerhub-deploy-on-host.yaml/badge.svg)](https://github.com/Mamdasn/telegram-bot-protests-in-berlin/actions/workflows/build-and-push-to-dockerhub-deploy-on-host.yaml)

Telegram bot: [@ProtestsBerlinBot:](https://t.me/ProtestsBerlinBot)

## Usage
After exporting the environmental variables `IP_ADDRESS` and `TG_BOT_TOKEN`, the docker instance is spawned by running `docker compose up --build -d`.

| PORT | USAGE |
|------|-------|
| 443  | Establish a connection with telegram server |
| 9051 | Send a request to tor control for a new ip |

IP rotation can be automated using crontab (in this case every 24 hours):
`0 */24 * * * echo -e 'AUTHENTICATE ""\r\nsignal NEWNYM\r\nQUIT' | nc localhost 9051`

## Documentation
The documentation can be found here: [Docs](https://mamdasn.github.io/telegram-bot-protests-in-berlin/)

## Donation
My ton coin wallet address: UQAqLrv2LMWy0gD6obOSCX9C5g_YCRvjjDqo7Ui1JYPz6aOh
