import os
import razorpay

KEY_ID = os.getenv("RAZORPAY_KEY_ID")
KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

client = None
if KEY_ID and KEY_SECRET:
    client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))

def create_order(amount_in_rupees: float, currency: str = "INR"):
    if not client:
        raise RuntimeError("Razorpay credentials not set")
    options = {"amount": int(amount_in_rupees * 100), "currency": currency, "receipt": f"receipt_{__import__('time').time()}"}
    return client.order.create(options)
