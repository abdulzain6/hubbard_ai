# Sales Roleplay Scenario API Documentation

## Authentication
Before accessing the endpoints, authenticate using the following credentials:

- **Email**: nitin@yopmail.com
- **Password**: Welcome@1
- **Login URL**: `https://api.themark.academy/backend/api/user/userLogin`
- **Token Usage**: Pass the obtained token in the `Authorization` header as `Bearer <token>`

---

## Base URL
```
/api/v1/scenarios
```

## Endpoints

### 1. Add Scenario
**POST `/`**

**Description:** Adds or updates a scenario in the database.

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "best_response": "string",
  "explanation": "string"
}
```

**Response:**
```json
{
  "name": "string",
  "description": "string",
  "best_response": "string",
  "explanation": "string"
}
```

**Authorization:** Admin

---

### 2. AI-Generate Scenario Metadata
**POST `/ai-generate`**

**Description:** Uses AI to generate scenario metadata.

**Request Body:**
```json
{
  "scenario": "string"
}
```

**Response:**
```json
{
  "metadata_key": "metadata_value"
}
```

**Authorization:** Any Authenticated User

---

### 3. Evaluate Scenario
**POST `/evaluate_scenario`**

**Description:** Evaluates a user's response based on the best response and explanation.

**Request Body:**
```json
{
  "scenario_name": "string",
  "salesman_response": "string"
}
```

**Response:**
```json
{
  "score": "number",
  "feedback": "string"
  .... more fields
}
```

**Authorization:** Any Authenticated User

---

### 4. Get Scenario by Name
**GET `/get_scenario/{name}`**

**Description:** Retrieves a scenario by its name.

**Response:**
```json
{
  "name": "string",
  "description": "string",
  "best_response": "string",
  "explanation": "string"
}
```

**Authorization:** Any Authenticated User

---

### 5. Update Scenario
**PUT `/update_scenario/{name}`**

**Description:** Updates a scenario's attributes.

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "best_response": "string",
  "explanation": "string"
}
```

**Response:**
```json
{
  "name": "string",
  "description": "string",
  "best_response": "string",
  "explanation": "string"
}
```

**Authorization:** Admin

---

### 6. Delete Scenario
**DELETE `/delete_scenario/{name}`**

**Description:** Deletes a scenario from the database.

**Response:**
```json
{
  "detail": "Scenario deleted successfully"
}
```

**Authorization:** Admin

---

### 7. Get All Scenarios
**GET `/get_all_scenarios`**

**Description:** Retrieves all scenarios from the database.

**Response:**
```json
[
  {
    "name": "string",
    "description": "string",
    "best_response": "string",
    "explanation": "string"
  }
]
```

**Authorization:** Any Authenticated User