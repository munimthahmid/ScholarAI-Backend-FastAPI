from app.models.message import MessageRequest, MessageResponse


def echo_message(req: MessageRequest) -> MessageResponse:
    return MessageResponse(echoed_message=f"You said: {req.message}")
