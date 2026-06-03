"""MiniApp AI Chat — proxy DeepSeek with function calling for cart/order actions."""
import json
import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from middleware.auth_middleware import get_current_user
from models.user import User
from models.cart_item import CartItem
from models.dish import Dish
from models.order import Order, OrderItem

router = APIRouter(prefix="/api/v1/miniapp/ai", tags=["miniapp-ai"])

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_dishes",
            "description": "Search dishes by keyword. Use when user asks about available dishes.",
            "parameters": {
                "type": "object",
                "properties": {"keyword": {"type": "string", "description": "Search keyword"}},
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cart",
            "description": "Get current shopping cart contents.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "Add a dish to the shopping cart. Call when user wants to order a dish.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dish_name": {"type": "string", "description": "Exact dish name from the menu"},
                    "quantity": {"type": "integer", "description": "Quantity, defaults to 1", "default": 1},
                },
                "required": ["dish_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_cart_item",
            "description": "Update quantity of a dish in cart. Set quantity to 0 to remove.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dish_name": {"type": "string", "description": "Dish name"},
                    "quantity": {"type": "integer", "description": "New quantity, 0 means remove"},
                },
                "required": ["dish_name", "quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_from_cart",
            "description": "Remove a dish from the shopping cart.",
            "parameters": {
                "type": "object",
                "properties": {"dish_name": {"type": "string", "description": "Dish name to remove"}},
                "required": ["dish_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_order_note",
            "description": "Add a note/remark to the order. E.g. less spicy, no cilantro.",
            "parameters": {
                "type": "object",
                "properties": {"note": {"type": "string", "description": "Order note"}},
                "required": ["note"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "place_order",
            "description": "Confirm and place the order. Cart must not be empty.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def _search_dishes(db: Session, keyword: str) -> str:
    dishes = db.query(Dish).filter(
        Dish.is_deleted == False,
        Dish.name.contains(keyword),
    ).limit(5).all()
    if not dishes:
        dishes = db.query(Dish).filter(
            Dish.is_deleted == False,
            (Dish.name.contains(keyword)) | (Dish.description.contains(keyword)),
        ).limit(5).all()
    if not dishes:
        return "No dishes found for: " + keyword
    lines = []
    for d in dishes:
        desc = f" - {d.description}" if d.description else ""
        lines.append(f"  id={d.id} | {d.name} | {d.price:.0f} yuan{desc}")
    return "\n".join(lines)


def _get_cart(db: Session, user_id: int) -> str:
    items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    if not items:
        return "Cart is empty"
    lines = []
    total = 0.0
    for item in items:
        subtotal = item.dish.price * item.quantity
        total += subtotal
        lines.append(f"  {item.dish.name} x{item.quantity} = {subtotal:.0f} yuan")
    lines.append(f"  Total: {total:.0f} yuan")
    return "\n".join(lines)


def _add_to_cart(db: Session, user_id: int, dish_name: str, quantity: int = 1) -> str:
    dish = db.query(Dish).filter(Dish.is_deleted == False, Dish.name == dish_name).first()
    if not dish:
        dish = db.query(Dish).filter(Dish.is_deleted == False, Dish.name.contains(dish_name)).first()
    if not dish:
        return f"Dish '{dish_name}' not found. Use search_dishes to find the correct name."
    existing = db.query(CartItem).filter(CartItem.user_id == user_id, CartItem.dish_id == dish.id).first()
    if existing:
        existing.quantity += quantity
        db.commit()
        return f"Updated '{dish.name}' quantity to {existing.quantity}"
    item = CartItem(user_id=user_id, dish_id=dish.id, quantity=quantity)
    db.add(item)
    db.commit()
    return f"Added '{dish.name}' x{quantity} to cart"


def _update_cart_item(db: Session, user_id: int, dish_name: str, quantity: int) -> str:
    dish = db.query(Dish).filter(Dish.is_deleted == False, Dish.name == dish_name).first()
    if not dish:
        dish = db.query(Dish).filter(Dish.is_deleted == False, Dish.name.contains(dish_name)).first()
    if not dish:
        return f"Dish '{dish_name}' not found"
    item = db.query(CartItem).filter(CartItem.user_id == user_id, CartItem.dish_id == dish.id).first()
    if not item:
        return f"'{dish.name}' is not in cart"
    if quantity <= 0:
        db.delete(item)
        db.commit()
        return f"Removed '{dish.name}' from cart"
    item.quantity = quantity
    db.commit()
    return f"Changed '{dish.name}' quantity to {quantity}"


def _remove_from_cart(db: Session, user_id: int, dish_name: str) -> str:
    return _update_cart_item(db, user_id, dish_name, 0)


def _set_order_note(db: Session, user_id: int, note: str) -> str:
    return f"Order note saved: {note}"


def _place_order(db: Session, user_id: int, order_note: str = "") -> str:
    cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    if not cart_items:
        return "Cart is empty, cannot place order. Please add dishes first."
    total = 0.0
    order_items = []
    names = []
    for ci in cart_items:
        subtotal = ci.dish.price * ci.quantity
        total += subtotal
        order_items.append(OrderItem(dish_id=ci.dish.id, dish_name=ci.dish.name, quantity=ci.quantity, unit_price=ci.dish.price, note=""))
        names.append(f"{ci.dish.name} x{ci.quantity}")
    order = Order(user_id=user_id, status="pending", total_amount=round(total, 2), note=order_note, items=order_items)
    db.add(order)
    db.query(CartItem).filter(CartItem.user_id == user_id).delete()
    db.commit()
    # Notify kitchen board via WebSocket
    from utils.ws_manager import kitchen_ws
    kitchen_ws.notify("new_order", {
        "order_id": order.id,
        "total_amount": order.total_amount,
        "status": order.status,
    })
    return f"Order placed! Items: {', '.join(names)}, Total: {total:.0f} yuan" + (f", Note: {order_note}" if order_note else "")


def _execute_tool(db: Session, user_id: int, tool_name: str, args: dict) -> str:
    mapping = {
        "search_dishes": lambda: _search_dishes(db, args.get("keyword", "")),
        "get_cart": lambda: _get_cart(db, user_id),
        "add_to_cart": lambda: _add_to_cart(db, user_id, args.get("dish_name", ""), args.get("quantity", 1)),
        "update_cart_item": lambda: _update_cart_item(db, user_id, args.get("dish_name", ""), args.get("quantity", 0)),
        "remove_from_cart": lambda: _remove_from_cart(db, user_id, args.get("dish_name", "")),
        "set_order_note": lambda: _set_order_note(db, user_id, args.get("note", "")),
        "place_order": lambda: _place_order(db, user_id),
    }
    fn = mapping.get(tool_name)
    return fn() if fn else f"Unknown tool: {tool_name}"


async def _handle_tool_calls(db: Session, user_id: int, messages: list, order_note: str) -> tuple:
    """Handle the tool-calling loop. Returns (stream_generator, updated_order_note)."""
    current_messages = [dict(m) for m in messages]  # deep copy
    first_round = True

    # Check if user's last message requests an action
    last_user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")
            break
    action_keywords = ["加", "来一份", "要一份", "下单", "点菜", "点一份", "帮我加",
                       "帮我下", "来一个", "要一个", "加个", "来个", "订", "结账",
                       "add", "order", "place", "buy", "我要", "给我", "帮我", "备注",
                       "改", "去掉", "不要", "删除", "移除", "换成"]

    needs_action = any(kw in last_user_msg for kw in action_keywords)

    for round_num in range(5):
        # Force tool_choice on first round if user clearly wants action
        tc = "required" if (needs_action and round_num == 0) else "auto"

        extra_instruction = ""
        if not first_round and round_num == 1 and not current_messages[-1].get("tool_calls"):
            extra_instruction = "你必须调用工具函数！不要只用文字回复。立即调用对应的工具！"
            tc = "required"

        payload_messages = list(current_messages)
        if extra_instruction:
            payload_messages.append({"role": "system", "content": extra_instruction})

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                DEEPSEEK_URL,
                headers={
                    "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": payload_messages,
                    "tools": TOOLS,
                    "tool_choice": tc,
                },
            )
            data = resp.json()
            choice = data["choices"][0]
            msg = choice["message"]

            if msg.get("tool_calls"):
                current_messages.append({
                    "role": "assistant",
                    "content": msg.get("content") or "",
                    "tool_calls": msg["tool_calls"],
                })

                for tc in msg["tool_calls"]:
                    func = tc["function"]
                    tool_name = func["name"]
                    try:
                        tool_args = json.loads(func["arguments"])
                    except json.JSONDecodeError:
                        tool_args = {}

                    if tool_name == "set_order_note":
                        order_note = tool_args.get("note", "")
                    if tool_name == "place_order" and order_note:
                        tool_args["order_note"] = order_note

                    result = _execute_tool(db, user_id, tool_name, tool_args)

                    current_messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result,
                    })
                first_round = False
                continue

            # No tool calls — check if we should force retry
            if first_round and any(kw in last_user_msg for kw in action_keywords):
                first_round = False
                # Don't add the AI's refusal to history; force retry with instruction
                continue

            # No tool calls — final text response
            break

    # Make a streaming call for the final response
    async def stream_final():
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                DEEPSEEK_URL,
                headers={
                    "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": current_messages,
                    "stream": True,
                    "temperature": 0.7,
                    "max_tokens": 800,
                },
            ) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk

    return stream_final(), order_note


@router.post("/chat")
async def ai_chat(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """AI chat with function calling for cart/order management."""
    messages = body.get("messages", [])

    stream_gen, _ = await _handle_tool_calls(db, current_user.id, messages, "")

    return StreamingResponse(
        stream_gen,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
