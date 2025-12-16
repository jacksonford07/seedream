# SeedDream API

A serverless API for the ByteDance SeedDream 4.5 image editing model via Fal.ai, hosted on Vercel.

## Features

- **Single Edit**: Edit images with custom prompts
- **Batch Processing**: Apply multiple outfits to multiple poses
- **Auto-download**: Results automatically download to your browser

## Deployment

### 1. Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/jacksonford07/seedream-api)

Or manually:

```bash
npm i -g vercel
vercel
```

### 2. Set Environment Variable

In your Vercel project settings, add:

- **Name**: `FAL_API_KEY`
- **Value**: Your API key from [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys)

## API Endpoints

### `GET /api/health`

Health check endpoint.

```json
{
  "status": "healthy",
  "fal_configured": true
}
```

### `POST /api/edit`

Edit images using SeedDream 4.5.

**Request Body:**
```json
{
  "prompt": "Your editing prompt",
  "images": ["data:image/png;base64,..."],
  "num_images": 1,
  "seed": 12345
}
```

**Response:**
```json
{
  "success": true,
  "images": [{"url": "https://..."}],
  "request_id": "..."
}
```

### `POST /api/batch`

Batch process poses × outfits.

**Request Body:**
```json
{
  "poses": [{"name": "pose1.png", "data": "base64..."}],
  "outfits": [{"name": "outfit1.png", "data": "base64..."}],
  "prompt": "Optional custom prompt",
  "seed": 12345
}
```

## Local Development

```bash
# Install dependencies
pip install fal-client

# Set API key
export FAL_API_KEY=your-key-here

# Run with Vercel CLI
vercel dev
```

## License

MIT
