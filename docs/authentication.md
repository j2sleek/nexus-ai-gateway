# Authentication and Authorization

## Supported Authentication Methods
- `Authorization: Bearer <api_key>`
- `X-API-Key: <api_key>`

## Permission Model
- `chat`
- `embeddings`
- `vision`
- `image_generation`
- `speech`
- `admin`

## Example Request
`curl -H "X-API-Key: your_key" http://localhost:8000/v1/models`
