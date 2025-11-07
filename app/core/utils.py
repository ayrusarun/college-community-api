from datetime import datetime


def time_ago(created_at: datetime) -> str:
    """Convert datetime to human readable time ago format."""
    now = datetime.utcnow()
    diff = now - created_at
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:  # Less than 1 hour
        minutes = int(seconds // 60)
        return f"{minutes} {'minute' if minutes == 1 else 'minutes'} ago"
    elif seconds < 86400:  # Less than 1 day
        hours = int(seconds // 3600)
        return f"{hours} {'hour' if hours == 1 else 'hours'} ago"
    elif seconds < 604800:  # Less than 1 week
        days = int(seconds // 86400)
        return f"{days} {'day' if days == 1 else 'days'} ago"
    else:
        weeks = int(seconds // 604800)
        if weeks < 4:
            return f"{weeks} {'week' if weeks == 1 else 'weeks'} ago"
        else:
            return created_at.strftime("%B %d, %Y")