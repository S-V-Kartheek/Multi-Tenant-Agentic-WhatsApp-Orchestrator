"""
seed_data.py — Populate MongoDB with Tenant A and Tenant B for development/demo.

Run this script once to set up the database:
  python seed_data.py

Tenant A: Luxury Furniture Store (Prestige Living)
Tenant B: Automotive Care (AutoElite Service Center)

Media URLs use publicly accessible placeholder files for demo purposes.
Replace with real assets before production.
"""
import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "whatsapp_agent")

# ── Tenant A: Luxury Furniture Store ──────────────────────────────────────────
TENANT_A = {
    "slug": "luxury-furniture",
    "name": "Prestige Living — Luxury Furniture",
    # phone_number_id stores the Twilio 'To' number for routing (without whatsapp: prefix)
    # During sandbox testing both tenants share the same Twilio number (+14155238886)
    "phone_number_id": os.getenv("TWILIO_WHATSAPP_NUMBER_TENANT_A", "+14155238886").replace("whatsapp:", ""),
    "whatsapp_token": os.getenv("TWILIO_AUTH_TOKEN", "PLACEHOLDER"),
    "system_prompt": (
        "You are Aria, the virtual concierge for *Prestige Living* — a premium luxury furniture brand. "
        "You speak with warmth, elegance, and expertise. Your goal is to help customers explore our collection, "
        "answer questions about quality and craftsmanship, and provide catalogs or product images when requested. "
        "Always maintain the brand's premium, sophisticated tone. Use tasteful emojis occasionally (🛋️ 🏠 ✨). "
        "Keep replies concise but impactful — quality over quantity."
    ),
    "media_library": {
        # PDFs
        "catalog":   "https://www.w3.org/WAI/WCAG21/Techniques/pdf/PDF1/fr.pdf",
        "brochure":  "https://www.w3.org/WAI/WCAG21/Techniques/pdf/PDF1/fr.pdf",
        "price list": "https://www.w3.org/WAI/WCAG21/Techniques/pdf/PDF1/fr.pdf",
        # Images
        "sofa":      "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800",
        "chair":     "https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?w=800",
        "table":     "https://images.unsplash.com/photo-1530018607912-eff2daa1bac4?w=800",
        "bedroom":   "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?w=800",
        "showroom":  "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800",
        "living room": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800",
    },
    "brand_color": "#8B7355",   # Warm walnut brown
}

# ── Tenant B: Automotive Care Center ──────────────────────────────────────────
TENANT_B = {
    "slug": "automotive-care",
    "name": "AutoElite Service Center",
    # phone_number_id stores the Twilio 'To' number for routing (without whatsapp: prefix)
    # During sandbox testing both tenants share the same Twilio number (+14155238886)
    "phone_number_id": os.getenv("TWILIO_WHATSAPP_NUMBER_TENANT_B", "+14155238886").replace("whatsapp:", ""),
    "whatsapp_token": os.getenv("TWILIO_AUTH_TOKEN", "PLACEHOLDER"),
    "system_prompt": (
        "You are Max, the virtual service advisor for *AutoElite Service Center*. "
        "You are knowledgeable, efficient, and trustworthy — like a master mechanic who explains things clearly. "
        "Help customers schedule appointments, provide service information, send invoices, and share repair diagrams. "
        "Use clear, professional language. Emojis are acceptable in moderation (🚗 🔧 ✅). "
        "When a customer asks about their vehicle's service status, invoices, or repair work, "
        "use your media tools to send the relevant documents or diagrams."
    ),
    "media_library": {
        # PDFs
        "invoice":      "https://www.w3.org/WAI/WCAG21/Techniques/pdf/PDF1/fr.pdf",
        "service sheet": "https://www.w3.org/WAI/WCAG21/Techniques/pdf/PDF1/fr.pdf",
        "warranty":     "https://www.w3.org/WAI/WCAG21/Techniques/pdf/PDF1/fr.pdf",
        "schedule":     "https://www.w3.org/WAI/WCAG21/Techniques/pdf/PDF1/fr.pdf",
        # Images
        "repair diagram": "https://images.unsplash.com/photo-1487754180451-c456f719a1fc?w=800",
        "engine":        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800",
        "tire":          "https://images.unsplash.com/photo-1542362567-b07e54358753?w=800",
        "workshop":      "https://images.unsplash.com/photo-1487754180451-c456f719a1fc?w=800",
        "car":           "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=800",
    },
    "brand_color": "#1E3A5F",   # Deep automotive navy blue
}


async def seed():
    """Insert or update both tenants in the database."""
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB_NAME]

    print("\nSeeding database...\n")

    for tenant_data in [TENANT_A, TENANT_B]:
        result = await db["tenants"].find_one_and_update(
            {"slug": tenant_data["slug"]},
            {"$set": tenant_data},
            upsert=True,
            return_document=True,
        )
        tenant_id = str(result["_id"])
        print(f"  [OK] Tenant '{tenant_data['name']}'")
        print(f"     ID: {tenant_id}")
        print(f"     Slug: {tenant_data['slug']}")
        print(f"     Media assets: {len(tenant_data['media_library'])}")
        print()

    # Ensure indexes are created for performance
    await db["chat_sessions"].create_index(
        [("tenant_id", 1), ("last_activity", -1)]
    )
    await db["chat_sessions"].create_index(
        [("customer_phone", 1), ("tenant_id", 1)], unique=True
    )
    await db["messages"].create_index([("session_id", 1), ("timestamp", 1)])
    await db["messages"].create_index([("tenant_id", 1), ("timestamp", -1)])

    print("  [OK] MongoDB indexes created")
    print("\n[DONE] Seeding complete! Both tenants are ready.\n")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
