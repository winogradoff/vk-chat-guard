# VK-Chat-Guard 

Python-скрипт (Heroku clock-процесс) для восстановления фотографии и названия беседы VK.

В переменных окружения (Config Variables для Heroku) должны быть заданы следущие значения:

```
VK_AUTH_TOKEN = <токен авторизации в VK>
VK_CHAT_ID = <ID беседы>
VK_CHAT_TITLE = <ожидаемое название беседы>
VK_SLEEP_SECONDS = <пауза перед chat_job (в секундах)>
VK_SCHEDULER_INTERVAL_SECONDS = <интервал chat_job (в секундах)>
```

Токен авторизации можно получить при переходе по следующему URL:

```
https://oauth.vk.com/authorize?client_id=<client_id>&scope=wall,messages,offline&redirect_uri=https://oauth.vk.com/blank.html&display=page&v=5.29&response_type=token
```

где `<client_id>` — идентификатор приложения VK.

Пауза `VK_SLEEP_SECONDS` для предотвращения частых запросов:

```python
sleep(self.sleep_time)
```

Проверка производится каждые `VK_SCHEDULER_INTERVAL_SECONDS` секунд:

```python
scheduler = BlockingScheduler()
scheduler.add_job(self.chat_job, 'interval', seconds=self.scheduler_interval)
scheduler.start()
```

Фотография беседы должна быть сохранена в файле `images/logo.png`.
