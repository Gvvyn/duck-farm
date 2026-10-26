# Duck Farm — Flask REST API + корзина

Учебный проект магазина фермерского утиного мяса. Сайт сохраняет главную страницу, историю фермы и каталог, а Flask предоставляет REST API.

## Возможности

- Каталог товаров с ценами в USD.
- Корзина: добавление, изменение количества, удаление позиции и очистка.
- Подсчёт количества товаров и общей суммы на сервере.
- SQLite для хранения товаров и корзин.
- JSON-ответы и HTTP-коды: 200, 201, 400, 404.
- Идентификатор корзины передаётся в заголовке `X-Cart-ID`.

## Запуск

В активированном виртуальном окружении:

```powershell
pip install -r requirements.txt
python app.py
```

Откройте http://127.0.0.1:5000/

SQLite-файл `duck_farm.db` создаётся автоматически рядом с `app.py`.

## API

| Метод | URL | Назначение |
|---|---|---|
| GET | `/api` | Список маршрутов API |
| GET | `/api/products` | Все товары |
| GET | `/api/products/1` | Один товар |
| GET | `/api/farm` | Информация о ферме |
| GET | `/api/cart` | Получить корзину |
| POST | `/api/cart/items` | Добавить товар |
| PATCH | `/api/cart/items/1` | Изменить количество |
| DELETE | `/api/cart/items/1` | Удалить товар из корзины |
| DELETE | `/api/cart` | Очистить корзину |

Для запросов корзины передавайте заголовок `X-Cart-ID` с постоянным идентификатором клиента. В веб-интерфейсе он автоматически создаётся и хранится в `localStorage`.

### Примеры PowerShell

Получить каталог:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/products
```

Создать ID корзины и добавить утиные грудки:

```powershell
$cartId = "student-cart-1"
$headers = @{ "X-Cart-ID" = $cartId }
$body = @{ product_id = 1; quantity = 2 } | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:5000/api/cart/items" `
  -Method Post `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $body
```

Получить корзину:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:5000/api/cart" `
  -Headers $headers
```

Установить количество грудок равным 3:

```powershell
$body = @{ quantity = 3 } | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:5000/api/cart/items/1" `
  -Method Patch `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $body
```

Удалить позицию:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:5000/api/cart/items/1" `
  -Method Delete `
  -Headers $headers
```

## Важно

- Цены учебные и указаны в долларах США.
- Оплата, оформление реального заказа, аккаунты и доставка не реализованы.
- Это учебный проект, не готовый к коммерческой эксплуатации.
- Если база уже создана, товары сохраняются между перезапусками. Начальные товары добавляются только при пустой таблице; для изменения старых цен обновите записи в SQLite или удалите `duck_farm.db` (это удалит сохранённые данные).
- Не запускайте встроенный сервер Flask с `debug=True` в публичной production-среде.
