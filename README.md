# URL Watchdog

A web-based URL monitoring application that watches URLs for specific keywords and sends notifications when matches are found.

## Features

- **URL Monitoring**: Monitor any URL for specific keywords
- **Flexible Scheduling**: Check URLs 1-24 times per day
- **Multiple Notification Channels**: 
  - Email (via SMTP)
  - Telegram (via Bot API)
  - Webhook (custom HTTP endpoints)
- **User Authentication**: JWT-based authentication
- **Subscription Model**: Free tier (3 monitors) and Pro tier (unlimited)
- **SSRF Protection**: Built-in security against server-side request forgery

## Project Structure

```
url-watchdog/
├── watchdog-backend/    # FastAPI backend
│   ├── app/
│   │   ├── main.py          # API endpoints
│   │   ├── auth.py          # Authentication
│   │   ├── database.py      # In-memory database
│   │   ├── models.py        # Data models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── scheduler.py     # Background job scheduler
│   │   ├── url_fetcher.py   # URL fetching with SSRF protection
│   │   ├── notifications.py # Notification handlers
│   │   └── stripe_service.py # Payment integration
│   └── pyproject.toml
└── watchdog-frontend/   # React frontend
    ├── src/
    │   ├── pages/           # Page components
    │   ├── lib/             # API client and auth context
    │   └── components/      # UI components
    └── package.json
```

## Setup

### Backend

```bash
cd watchdog-backend

# Install dependencies
poetry install

# Create .env file
cp .env.example .env
# Edit .env with your settings

# Run development server
poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd watchdog-frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env

# Run development server
npm run dev
```

## Environment Variables

### Backend (.env)

```
JWT_SECRET_KEY=your-secret-key-change-in-production
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
```

### Frontend (.env)

```
VITE_API_URL=http://localhost:8000
```

## Deployment

### Backend
Deploy to any Python hosting service (Heroku, Railway, Render, Fly.io, etc.)

### Frontend
1. Update `VITE_API_URL` in `.env` with your deployed backend URL
2. Build: `npm run build`
3. Deploy the `dist` folder to any static hosting (Vercel, Netlify, etc.)

## API Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user
- `POST /api/monitors` - Create monitor
- `GET /api/monitors` - List monitors
- `GET /api/monitors/{id}` - Get monitor
- `PUT /api/monitors/{id}` - Update monitor
- `DELETE /api/monitors/{id}` - Delete monitor
- `POST /api/monitors/{id}/check` - Trigger manual check
- `GET /api/monitors/{id}/logs` - Get check logs
- `POST /api/notifications` - Create notification channel
- `GET /api/notifications` - List notification channels
- `PUT /api/notifications/{id}` - Update notification channel
- `DELETE /api/notifications/{id}` - Delete notification channel
- `POST /api/billing/checkout` - Create Stripe checkout session
- `POST /api/billing/portal` - Create Stripe billing portal session

## Note

This is a proof-of-concept using an in-memory database. Data will be lost when the server restarts. For production use, implement a persistent database (PostgreSQL, MongoDB, etc.).

## License

MIT
