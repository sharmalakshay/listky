# Configuration Files

This directory contains configuration files for different deployment scenarios.

## Files

- `Dockerfile` - Docker container configuration for the core platform
- `docker-compose.yaml` - Container orchestration for self-hosting
- `.env.example` - Environment variables template

## Deployment Scenarios

### 1. Core Platform Only (Open Source)
Use the files in this directory as-is. This gives you the full listky.top experience
with all core features:
- User accounts and authentication
- List creation and management  
- Privacy-preserving view tracking
- Trending lists
- Voting system (when implemented)

### 2. Core + Premium Features (Hybrid)
If you have access to the premium features repository:

1. Set `ENABLE_PREMIUM_FEATURES=true` in your `.env`
2. Enable specific plugins you want: `PLUGIN_ANALYTICS_ENABLED=true` etc.
3. The plugin system will automatically load premium features

Premium features include:
- Advanced analytics dashboard
- Enhanced SEO optimization
- Rich social media previews  
- Enterprise collaboration tools
- Commercial API access

### 3. Development Setup

For local development:

```bash
# Copy and edit environment file
cp .env.example .env
# Edit .env with your settings

# Run with Docker Compose
docker compose up -d --build

# Or run locally with Python
pip install -r ../requirements.txt
cd ..
uvicorn main:app --reload
```

## Plugin Architecture

The core platform emits events at key points:
- `user_created` - When someone signs up
- `user_login` - When someone logs in  
- `list_created` - When a list is created
- `list_viewed` - When someone views a public list
- `list_updated` - When a list is edited
- `list_deleted` - When a list is removed

Premium plugins can register hooks for these events to provide enhanced functionality
without modifying the core codebase.

See `core/plugins.py` for the full plugin system documentation.