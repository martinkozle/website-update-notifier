import time
import json
from typing import List, Optional

import requests
import difflib
from dhooks import Webhook
from bs4 import BeautifulSoup


def request_text(url: str) -> Optional[str]:
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)
        return text
    except requests.exceptions.RequestException as err:
        print(err)
        return None


class NotificationWebhook:
    def __init__(
        self, webhook_url: str,
        urls: List[str],
        username: str = 'Website-update-notifier NOTIFICATION'
    ):
        self.webhook_url = webhook_url
        self.urls = urls
        self.webhook = Webhook(webhook_url, username=username)
        self.html_dict = {}

    def send(self, message):
        self.webhook.send(message)

    def send_blocks(self, output: str, formatting: str = ''):
        while len(output):
            find_chars = ['\n', ' ', ',']
            index = len(output)
            if index > 1900:
                for find_char in find_chars:
                    index = output[:1900].rfind(find_char) + 1
                    if index:
                        break
                else:
                    index = 1900
            out = f'```{formatting}\n{output[:index]}```'
            self.send(out)
            output = output[index:]

    def send_notification(self, url: str, diff: str):
        message = f'Change detected: \n{url}'
        self.send(message)
        self.send_blocks(diff, formatting='diff')

    def check_updates(self):
        for url in self.urls:
            text = request_text(url)
            if text:
                if url not in self.html_dict:
                    self.html_dict[url] = text
                elif self.html_dict[url] != text:
                    diff = '\n'.join(
                        filter(
                            lambda s: not s.startswith('  '),
                            difflib.ndiff(
                                self.html_dict[url].split('\n'),
                                text.split('\n')
                            )
                        )
                    )
                    self.html_dict[url] = text
                    self.send_notification(url, diff)


def load_config() -> dict:
    with open('config/config.json', 'r') as f:
        config = json.load(f)
    return config


def main():
    config = load_config()
    notification_webhooks = [
        NotificationWebhook(webhook['webhook'], webhook['urls'])
        for webhook in config['webhooks']
    ]
    count = 1
    try:
        while True:
            print(f'{count=}')
            count += 1
            for notification_webhook in notification_webhooks:
                notification_webhook.check_updates()
            time.sleep(config['sleep'])
    except KeyboardInterrupt:
        print('\nExiting...')


if __name__ == '__main__':
    main()
