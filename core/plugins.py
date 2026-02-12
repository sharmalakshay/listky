"""
Plugin system for listky.top

This module provides hooks for premium features to extend core functionality
without modifying the open source core code.

Premium features can register hooks to:
- Track additional analytics
- Add enhanced SEO metadata
- Provide advanced search capabilities
- Implement enterprise features

The core platform emits events at key points, and premium plugins can listen
to these events to provide enhanced functionality.
"""

from typing import Dict, List, Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Plugin registry
_plugins: Dict[str, List[Callable]] = {}
_plugin_config: Dict[str, Any] = {}

def register_hook(event: str, callback: Callable):
    """
    Register a callback function to be called when an event occurs.
    
    Args:
        event: Event name (e.g., 'user_created', 'list_viewed')
        callback: Function to call when event occurs
    """
    if event not in _plugins:
        _plugins[event] = []
    _plugins[event].append(callback)
    logger.info(f"Registered plugin hook for event: {event}")

def emit_event(event: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Emit an event to all registered plugins.
    
    Args:
        event: Event name
        data: Event data to pass to plugins
        
    Returns:
        Updated data (plugins can modify the data)
    """
    if event not in _plugins:
        return data
    
    logger.debug(f"Emitting event: {event}")
    for callback in _plugins[event]:
        try:
            result = callback(data)
            # If callback returns data, update our data dict
            if result and isinstance(result, dict):
                data.update(result)
        except Exception as e:
            logger.error(f"Plugin hook error for event {event}: {e}")
            # Continue with other plugins even if one fails
            continue
    
    return data

def configure_plugin(plugin_name: str, config: Dict[str, Any]):
    """Configure a plugin with settings"""
    _plugin_config[plugin_name] = config
    logger.info(f"Configured plugin: {plugin_name}")

def get_plugin_config(plugin_name: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a plugin"""
    return _plugin_config.get(plugin_name)

def is_plugin_enabled(plugin_name: str) -> bool:
    """Check if a plugin is enabled"""
    config = get_plugin_config(plugin_name)
    if not config:
        return False
    return config.get('enabled', False)

# Core events that premium plugins can hook into:

def on_user_created(username: str, client_ip: str, **kwargs):
    """Called when a new user account is created"""
    return emit_event('user_created', {
        'username': username,
        'client_ip': client_ip,
        **kwargs
    })

def on_user_login(username: str, client_ip: str, **kwargs):
    """Called when a user logs in"""
    return emit_event('user_login', {
        'username': username,
        'client_ip': client_ip,
        **kwargs
    })

def on_list_created(username: str, slug: str, title: str, is_public: bool, **kwargs):
    """Called when a new list is created"""
    return emit_event('list_created', {
        'username': username,
        'slug': slug,
        'title': title,
        'is_public': is_public,
        **kwargs
    })

def on_list_viewed(username: str, slug: str, viewer_ip: str, **kwargs):
    """Called when a list is viewed"""
    return emit_event('list_viewed', {
        'username': username,
        'slug': slug,
        'viewer_ip': viewer_ip,
        **kwargs
    })

def on_list_updated(username: str, slug: str, title: str, **kwargs):
    """Called when a list is updated"""
    return emit_event('list_updated', {
        'username': username,
        'slug': slug,
        'title': title,
        **kwargs
    })

def on_list_deleted(username: str, slug: str, **kwargs):
    """Called when a list is deleted"""
    return emit_event('list_deleted', {
        'username': username,
        'slug': slug,
        **kwargs
    })

# Hook for enhancing web responses (SEO, analytics, etc.)
def enhance_web_response(response_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Called when generating web responses to allow plugins to add:
    - SEO meta tags
    - Analytics tracking codes  
    - Social media previews
    - Enhanced CSS/JS
    """
    return emit_event('enhance_web_response', {
        'response_type': response_type,
        'data': data
    })

# Example premium plugin registration (would be in premium repo):
"""
# In premium/analytics.py:

from core.plugins import register_hook

def track_advanced_analytics(event_data):
    # Track detailed analytics for premium features
    username = event_data.get('username')
    # ... analytics code ...
    return event_data

def enhance_seo_metadata(event_data):
    # Add rich SEO metadata for public lists
    if event_data.get('response_type') == 'list_view':
        event_data['meta_tags'] = [
            '<meta property="og:title" content="...">',
            '<meta property="og:description" content="...">',
        ]
    return event_data

# Register the hooks
register_hook('list_viewed', track_advanced_analytics)
register_hook('enhance_web_response', enhance_seo_metadata)
"""