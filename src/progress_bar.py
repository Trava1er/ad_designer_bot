"""
Progress bar visualization for ad statuses.
Shows visual representation: Created → Paid → Moderation → Published
"""

from typing import Dict, Optional


def get_status_emoji(status: str, current_status: str) -> str:
    """
    Get emoji for status based on completion.
    
    Args:
        status: Status to check
        current_status: Current ad status
        
    Returns:
        Emoji representing completion state
    """
    status_order = ["draft", "pending", "approved", "published"]
    
    try:
        status_index = status_order.index(status)
        current_index = status_order.index(current_status)
        
        if status_index < current_index:
            return "✅"  # Completed
        elif status_index == current_index:
            return "🔄"  # In progress
        else:
            return "⏳"  # Pending
    except ValueError:
        return "❓"  # Unknown


def get_progress_bar(current_status: str, language: str = "ru") -> str:
    """
    Generate progress bar visualization for ad status.
    
    Args:
        current_status: Current ad status (draft, pending, approved, published)
        language: User language (ru, en, zh-tw)
        
    Returns:
        Formatted progress bar string
    """
    # Status labels by language
    labels = {
        "ru": {
            "draft": "Создано",
            "pending": "Модерация",
            "approved": "Одобрено",
            "published": "Опубликовано"
        },
        "en": {
            "draft": "Created",
            "pending": "Moderation",
            "approved": "Approved",
            "published": "Published"
        },
        "zh-tw": {
            "draft": "已創建",
            "pending": "審核中",
            "approved": "已批准",
            "published": "已發布"
        }
    }
    
    status_labels = labels.get(language, labels["ru"])
    statuses = ["draft", "pending", "approved", "published"]
    
    # Build progress bar
    progress_parts = []
    
    for status in statuses:
        emoji = get_status_emoji(status, current_status)
        label = status_labels.get(status, status)
        progress_parts.append(f"{emoji} {label}")
    
    # Join with arrows
    progress_bar = " → ".join(progress_parts)
    
    return progress_bar


def get_detailed_progress(current_status: str, payment_status: Optional[str], language: str = "ru") -> str:
    """
    Generate detailed progress with payment status.
    
    Args:
        current_status: Current ad status
        payment_status: Payment status (pending, paid, failed, cancelled)
        language: User language
        
    Returns:
        Detailed progress string with payment info
    """
    # Payment status labels
    payment_labels = {
        "ru": {
            "pending": "💳 Ожидает оплаты",
            "paid": "✅ Оплачено",
            "failed": "❌ Ошибка оплаты",
            "cancelled": "🚫 Отменено"
        },
        "en": {
            "pending": "💳 Awaiting payment",
            "paid": "✅ Paid",
            "failed": "❌ Payment failed",
            "cancelled": "🚫 Cancelled"
        },
        "zh-tw": {
            "pending": "💳 等待付款",
            "paid": "✅ 已付款",
            "failed": "❌ 付款失敗",
            "cancelled": "🚫 已取消"
        }
    }
    
    # Get basic progress bar
    progress = get_progress_bar(current_status, language)
    
    # Add payment status if provided
    if payment_status:
        payment_text = payment_labels.get(language, payment_labels["ru"]).get(
            payment_status, payment_status
        )
        progress = f"{payment_text}\n\n{progress}"
    
    return progress


def get_progress_percentage(current_status: str) -> int:
    """
    Get progress percentage based on status.
    
    Args:
        current_status: Current ad status
        
    Returns:
        Progress percentage (0-100)
    """
    status_progress = {
        "draft": 25,
        "pending": 50,
        "approved": 75,
        "published": 100,
        "rejected": 0
    }
    
    return status_progress.get(current_status, 0)


def get_visual_progress_bar(current_status: str, width: int = 20) -> str:
    """
    Generate visual ASCII progress bar.
    
    Args:
        current_status: Current ad status
        width: Width of progress bar in characters
        
    Returns:
        Visual progress bar: [████████░░░░░░░░░░░░] 40%
    """
    percentage = get_progress_percentage(current_status)
    filled = int((percentage / 100) * width)
    empty = width - filled
    
    bar = "█" * filled + "░" * empty
    return f"[{bar}] {percentage}%"


def get_status_description(current_status: str, language: str = "ru") -> str:
    """
    Get description of current status.
    
    Args:
        current_status: Current ad status
        language: User language
        
    Returns:
        Status description
    """
    descriptions = {
        "ru": {
            "draft": "📝 Черновик создан. Ожидает оплаты для публикации.",
            "pending": "⏳ На модерации. Проверка займет до 2 часов.",
            "approved": "✅ Одобрено! Скоро будет опубликовано.",
            "published": "🎉 Опубликовано и доступно аудитории!",
            "rejected": "❌ Отклонено модератором. Проверьте требования."
        },
        "en": {
            "draft": "📝 Draft created. Awaiting payment for publishing.",
            "pending": "⏳ Under moderation. Review takes up to 2 hours.",
            "approved": "✅ Approved! Will be published soon.",
            "published": "🎉 Published and available to audience!",
            "rejected": "❌ Rejected by moderator. Check requirements."
        },
        "zh-tw": {
            "draft": "📝 草稿已創建。等待付款以發布。",
            "pending": "⏳ 審核中。審核需要最多2小時。",
            "approved": "✅ 已批准！即將發布。",
            "published": "🎉 已發布並向受眾開放！",
            "rejected": "❌ 被審核員拒絕。檢查要求。"
        }
    }
    
    return descriptions.get(language, descriptions["ru"]).get(
        current_status, "Unknown status"
    )


# Example usage:
if __name__ == "__main__":
    print("=== Progress Bar Examples ===\n")
    
    statuses = ["draft", "pending", "approved", "published"]
    
    for status in statuses:
        print(f"\nStatus: {status}")
        print(get_progress_bar(status, "ru"))
        print(get_visual_progress_bar(status))
        print(get_status_description(status, "ru"))
        print("-" * 50)
