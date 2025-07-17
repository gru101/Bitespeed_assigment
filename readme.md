# BiteSpeed Identity Reconciliation Service

This is a Django project that implements the BiteSpeed contact identity reconciliation service.

It exposes a single POST endpoint:


## Tech Stack
- Python
- Django
- SQLite 
- Deployed on [Render](https://render.com)

---

## API Endpoint

### POST `/identity`

#### Request body:
```json
{
  "email": "example@domain.com",     // optional
  "phoneNumber": "1234567890"        // optional
}
