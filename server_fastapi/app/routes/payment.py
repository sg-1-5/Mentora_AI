
from fastapi import APIRouter, Depends, HTTPException
from app.routes.auth import get_current_user
from app.services.razorpay_service import create_order as rp_create_order
from app.db import mongo
import hmac
import hashlib
from bson import ObjectId

router = APIRouter()


@router.post("/create-order")
async def create_order(data: dict, current_user=Depends(get_current_user)):
    plan_id = data.get("planId")
    amount = data.get("amount")
    credits = data.get("credits")
    if not amount or not credits:
        raise HTTPException(status_code=400, detail="Invalid plan data")
    try:
        order = rp_create_order(amount)
        await mongo.db.payments.insert_one({
            "userId": ObjectId(current_user["id"]),
            "planId": plan_id,
            "amount": amount,
            "credits": credits,
            "razorpayOrderId": order.get("id"),
            "status": "created"
        })
        return order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/order")
async def create_order_alias(data: dict, current_user=Depends(get_current_user)):
    return await create_order(data, current_user)


@router.post("/verify")
async def verify_payment(data: dict, current_user=Depends(get_current_user)):
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature = data.get("razorpay_signature")
    if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
        raise HTTPException(status_code=400, detail="Missing payment fields")

    secret = __import__("os").environ.get("RAZORPAY_KEY_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="Razorpay secret not configured")

    body = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected_signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    if expected_signature != razorpay_signature:
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    payment = await mongo.db.payments.find_one({"razorpayOrderId": razorpay_order_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.get("status") == "paid":
        return {"message": "Already processed"}

    await mongo.db.payments.update_one({"_id": payment.get("_id")}, {"$set": {"status": "paid", "razorpayPaymentId": razorpay_payment_id}})
    updated = await mongo.db.users.find_one_and_update({"_id": payment.get("userId")}, {"$inc": {"credits": payment.get("credits", 0)}}, return_document=True)

    return {
        "success": True,
        "message": "Payment verified and credits added",
        "user": {
            "_id": str(updated.get("_id")),
            "id": str(updated.get("_id")),
            "name": updated.get("name"),
            "email": updated.get("email"),
            "credits": updated.get("credits"),
        },
    }
