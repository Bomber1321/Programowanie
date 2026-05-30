from db.repository import get_task_by_title


def validate_title(title):
    title = title.strip()
    if len(title) < 3:
        return "Title has to have at least 3 chars."
    existing_task = get_task_by_title(title)
    if existing_task:
        return f"There is already task with title: {title}"
    return None