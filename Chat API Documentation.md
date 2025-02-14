# Chat API Documentation

## Endpoints

### 1. Stream Chat
`POST /chat-stream`

Creates a streaming chat session with an AI model.

#### Request Body
```json
{
  "question": "string",
  "chat_history": [["string", "string"]] | null,
  "role": "string" | null,
  "chat_session_id": "string" | null
}
```

- `question`: The user's input message
- `chat_history`: Optional array of tuples containing previous [human_message, ai_message] pairs
- `role`: Optional role identifier to use specific prompt prefixes
- `chat_session_id`: Optional identifier for maintaining chat sessions

#### Response
Streams AI responses as chunks of text data.

### 2. Get Chat History for Session
`GET /chat-history/{chat_session_id}`

Retrieves the complete chat history for a specific chat session.

#### Path Parameters
- `chat_session_id`: The unique identifier of the chat session

#### Response
```json
{
  "chat_session_id": "string",
  "user_id": "string",
  "topic": "string",
  "chat_history": [["string", "string"]]
}
```

### 3. Get User's Chat History
`GET /chat-history/`

Retrieves a list of all chat sessions for the authenticated user.

#### Response
```json
[
  {
    "chat_session_id": "string",
    "user_id": "string",
    "topic": "string"
  }
]
```

### 4. Delete Chat History
`DELETE /chat-history/{chat_session_id}`

Deletes a specific chat session and its history.

#### Path Parameters
- `chat_session_id`: The unique identifier of the chat session to delete

#### Response
```json
{
  "message": "Chat history deleted successfully"
}
```

## Authentication
All endpoints require user authentication. The API expects user credentials to be provided through the authentication middleware.

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Role not found."
}
```

### 404 Not Found
```json
{
  "detail": "Chat history not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error message"
}
```

## Features
- Streaming responses for real-time chat interaction
- Persistent chat history storage
- Role-based prompting
- Automatic topic generation for new conversations
- Thread-safe implementation using queue system
- Support for continuation of existing conversations
- Background task processing for non-blocking operations

## Notes
- The API uses OpenAI's chat models through LangChain
- Chat sessions are user-specific and persisted in a database
- Streaming responses have a 60-second timeout
- The API supports custom roles with specific prompt prefixes