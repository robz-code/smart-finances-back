# Contacts API Documentation

The Contacts API allows users to manage their contacts and view debt relationships between users.

## Endpoints

### POST /contacts
Create a new contact for the current user.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john.doe@example.com"
}
```

**Behavior:**
- If the contact email is already registered, creates a relationship between users
- If the contact email is not registered, creates a new inactive user and relationship
- Cannot add yourself as a contact

**Response:**
```json
{
  "id": "uuid",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "is_registered": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### GET /contacts
Get all contacts for the current user.

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "is_registered": false,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### GET /contacts/{contact_id}
Get detailed information about a specific contact including debt information.

**Response:**
```json
{
  "contact": {
    "id": "uuid",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "is_registered": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "debts": [
    {
      "id": "uuid",
      "amount": 100.50,
      "type": "lent",
      "note": "Lunch payment",
      "date": "2024-01-01T00:00:00Z",
      "from_user_id": "uuid",
      "to_user_id": "uuid"
    }
  ]
}
```

## Authentication

All endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <your_token>
```

## Business Logic

1. **Contact Creation**: When creating a contact, the system checks if the email already exists:
   - If yes: Creates a relationship between the current user and existing user
   - If no: Creates a new inactive user and then creates the relationship

2. **Debt Information**: The contact detail endpoint shows all debts between the current user and the contact, regardless of who owes whom.

3. **User Registration**: Contacts created from non-registered emails are marked as inactive users (`is_registered: false`) and can be activated later if they register with the same email.

## Error Handling

- **400 Bad Request**: Invalid data or trying to add yourself as a contact
- **404 Not Found**: Contact not found
- **409 Conflict**: Contact relationship already exists
- **500 Internal Server Error**: Database or server errors