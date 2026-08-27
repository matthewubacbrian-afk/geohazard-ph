def queue_push_notification(subscription_id: str, message: str) -> dict[str, str]:
    return {"subscription_id": subscription_id, "message": message, "status": "queued"}
