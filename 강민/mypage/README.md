# Mypage Mock Frontend + Backend

This folder contains the first mypage mock implementation.
The frontend is served by a local Node.js mock backend so the page already uses API-like calls.

## Run

Run this command from the project root.

```powershell
node .\mypage_mock_server.js
```

Open this URL in a browser.

```text
http://localhost:5174
```

## Implemented Scope

- Mypage summary
- Profile read
- Profile update
- Order list
- Order detail
- Order detail action placeholders for payment/cancel flow
- Payment history list
- Payment detail
- Wishlist list
- Wishlist remove/restore
- Recently viewed products

## Mock API

- `GET /api/mypage/summary`
- `GET /api/mypage/profile`
- `PATCH /api/mypage/profile`
- `GET /api/mypage/orders`
- `GET /api/mypage/orders/{orderId}`
- `GET /api/mypage/payments`
- `GET /api/mypage/payments/{paymentId}`
- `GET /api/mypage/wishlist`
- `DELETE /api/mypage/wishlist/{productId}`
- `GET /api/mypage/recent-products`
- `POST /api/mypage/reset`

## Notes

- Auth is mocked with the `X-Mock-User: 1` header.
- Data changes are stored only in server memory.
- Restarting the server or pressing Reset restores the initial mock data.
- The order/payment execution itself remains owned by the order/payment domains.
