Сформируй следующую json структуру для ответа по api, основываясь на содержимом текстовых файлов. Нельзя убирать или добавлять поля, если ты не можешь заполнить какое-то поле, подставь туда пустое значение. Верни результат в формате:

```json
{
  "profile": {
    "name": "...",
    "club": "...",
    ...
  }
}
```

```json
{
  "profile": {
    "name": "Евгения Шумакова",
    "club": "HEMA TEAM",
    "country": "Russia",
    "location": "Saint Petersburg",
    "summary": {
      "events": 9,
      "categories": 10,
      "fights": 51
    },
    "weapons": [
      {
        "name": "Longsword - Women",
        "rank": 53,
        "rating": 1539,
        "events": 10,
        "fights": 51,
        "win_percent": 49
      }
    ],
    "fights": [
      {
        "opponent": "Дарья Муравьева",
        "club": "CounterTime",
        "user_score": 7,
        "opponent_score": 8,
        "result": "lose",
        "tournament": "Primavera XIII",
        "stage": "Upper bracket, Round 4, fight 1",
        "date": "Mar 14, 2026",
        "weapon": "Longsword - Women"
      }
    ],
    "tournaments": [
      {
        "name": "Primavera XIII",
        "url": "/tournament/primavera-13",
        "slug": "primavera-13",
        "category": "Длинный меч, лига Advanced",
        "vk_link": ""
      }
    ]
  }
}
```
Содержимое файлов:
{__filecontent__}