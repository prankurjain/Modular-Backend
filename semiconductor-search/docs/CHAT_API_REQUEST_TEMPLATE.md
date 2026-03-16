# ST Chat API Request Template (Corrected)

Use this payload format for chat requests to:

`POST https://chat.st.com/api/client-apps`

## JSON payload

```json
{
  "version": 1,
  "clientAppName": "stm32-cube-client-app",
  "timestamp": 1725996984081,
  "remoteUser": "john.smith@st.com",
  "service": "chat",
  "temperature": 0.2,
  "maxResponseTokens": 4096,
  "responseFormat": "json_object",
  "persona": "st_copilot",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "content": "Describe that image"
        },
        {
          "type": "image",
          "content": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgA..."
        }
      ]
    }
  ]
}
```

## Notes

- `responseFormat` should be either:
  - `"text"`, or
  - `"json_object"`.
- `messages[].content` is an array, where each item has:
  - `type`: `"text"` or `"image"`
  - `content`: string payload.
- For authenticated calls, include headers:
  - `stchatgpt-auth-token`
  - `stchatgpt-auth-nonce`
  - `Content-Type: application/json`
- Token generation follows the same SHA1 pattern already used in this codebase:
  - `sha1("{clientAppName}_{service}_{apiKey}_{timestamp}_{nonce}")`.
