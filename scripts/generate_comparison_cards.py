#!/usr/bin/env python3
"""
Generate comparison cards showing multiple tariff options.
Simplified version with Latin text only.
"""

from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = "images/tariffs"
CARD_W = 350
CARD_H = 500
SPACING = 30
TOTAL_W = (CARD_W * 3) + (SPACING * 4)
TOTAL_H = CARD_H + (SPACING * 2) + 80

# Colors
BG = (255, 255, 255)
PRIMARY = (43, 82, 120)
SUCCESS = (81, 207, 102)
TEXT = (44, 62, 80)
GRAY = (236, 240, 241)
CARD_BG = (250, 250, 250)


def create_comparison(tariffs, title_text, filename):
    """Create comparison card."""
    img = Image.new('RGB', (TOTAL_W, TOTAL_H), BG)
    draw = ImageDraw.Draw(img)
    
    # Fonts
    try:
        font_main = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 40)
        font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 26)
        font_price = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 36)
        font_text = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 20)
        font_small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 16)
    except:
        font_main = ImageFont.load_default()
        font_title = ImageFont.load_default()
        font_price = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Main title
    title_bbox = draw.textbbox((0, 0), title_text, font=font_main)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((TOTAL_W - title_w) // 2, SPACING), title_text, fill=PRIMARY, font=font_main)
    
    y_offset = SPACING + 70
    
    # Draw each card
    for i, tariff in enumerate(tariffs):
        x = SPACING + (i * (CARD_W + SPACING))
        
        # Shadow
        draw.rounded_rectangle(
            [(x + 5, y_offset + 5), (x + CARD_W + 5, y_offset + CARD_H + 5)],
            radius=12,
            fill=(200, 200, 200)
        )
        
        # Card
        border = PRIMARY if tariff.get("highlight") else GRAY
        draw.rounded_rectangle(
            [(x, y_offset), (x + CARD_W, y_offset + CARD_H)],
            radius=12,
            fill=CARD_BG,
            outline=border,
            width=2
        )
        
        cy = y_offset + 20
        
        # Badge
        if tariff.get("badge"):
            badge = tariff["badge"]
            badge_bbox = draw.textbbox((0, 0), badge, font=font_small)
            badge_w = badge_bbox[2] - badge_bbox[0]
            badge_x = x + (CARD_W - badge_w) // 2 - 8
            
            draw.rounded_rectangle(
                [(badge_x, cy), (badge_x + badge_w + 16, cy + 22)],
                radius=8,
                fill=SUCCESS
            )
            draw.text((badge_x + 8, cy + 2), badge, fill=BG, font=font_small)
            cy += 32
        
        # Title
        title = tariff["title"]
        title_bbox = draw.textbbox((0, 0), title, font=font_title)
        title_w = title_bbox[2] - title_bbox[0]
        draw.text((x + (CARD_W - title_w) // 2, cy), title, fill=PRIMARY, font=font_title)
        cy += 40
        
        # Subtitle
        sub = tariff["subtitle"]
        sub_bbox = draw.textbbox((0, 0), sub, font=font_text)
        sub_w = sub_bbox[2] - sub_bbox[0]
        draw.text((x + (CARD_W - sub_w) // 2, cy), sub, fill=TEXT, font=font_text)
        cy += 45
        
        # Line
        draw.line([(x + 20, cy), (x + CARD_W - 20, cy)], fill=GRAY, width=1)
        cy += 25
        
        # Price
        price = tariff["price"]
        price_bbox = draw.textbbox((0, 0), price, font=font_price)
        price_w = price_bbox[2] - price_bbox[0]
        draw.text((x + (CARD_W - price_w) // 2, cy), price, fill=PRIMARY, font=font_price)
        cy += 50
        
        # Save
        if tariff.get("save"):
            save_txt = f"Save {tariff['save']}%"
            save_bbox = draw.textbbox((0, 0), save_txt, font=font_small)
            save_w = save_bbox[2] - save_bbox[0]
            save_x = x + (CARD_W - save_w) // 2 - 8
            
            draw.rounded_rectangle(
                [(save_x, cy), (save_x + save_w + 16, cy + 22)],
                radius=6,
                fill=SUCCESS
            )
            draw.text((save_x + 8, cy + 2), save_txt, fill=BG, font=font_small)
            cy += 35
        
        # Line
        draw.line([(x + 20, cy), (x + CARD_W - 20, cy)], fill=GRAY, width=1)
        cy += 20
        
        # Features
        for feature in tariff["features"]:
            draw.text((x + 25, cy), feature, fill=TEXT, font=font_text)
            cy += 28
    
    img.save(filename, 'PNG', quality=95)
    print(f"✓ {filename}")


def main():
    print("🎨 Generating comparison cards...")
    print()
    
    # One-time comparison (show 3 popular options)
    onetime_rub = [
        {
            "title": "📦 5 ADS",
            "subtitle": "5 ads",
            "price": "900 RUB",
            "save": 10,
            "features": ["AI", "Placement", "Statistics"]
        },
        {
            "title": "🔥 10 ADS",
            "subtitle": "10 ads",
            "price": "1600 RUB",
            "save": 20,
            "badge": "Popular",
            "highlight": True,
            "features": ["AI", "Placement", "Statistics"]
        },
        {
            "title": "🔥 20 ADS",
            "subtitle": "20 ads",
            "price": "3000 RUB",
            "save": 25,
            "features": ["AI", "Placement", "Statistics"]
        }
    ]
    
    onetime_usd = [
        {
            "title": "📦 5 ADS",
            "subtitle": "5 ads",
            "price": "$13",
            "save": 10,
            "features": ["AI", "Placement", "Statistics"]
        },
        {
            "title": "🔥 10 ADS",
            "subtitle": "10 ads",
            "price": "$24",
            "save": 20,
            "badge": "Popular",
            "highlight": True,
            "features": ["AI", "Placement", "Statistics"]
        },
        {
            "title": "🔥 20 ADS",
            "subtitle": "20 ads",
            "price": "$45",
            "save": 25,
            "features": ["AI", "Placement", "Statistics"]
        }
    ]
    
    onetime_usdt = [
        {
            "title": "📦 5 ADS",
            "subtitle": "5 ads",
            "price": "13 USDT",
            "save": 10,
            "features": ["AI", "Placement", "Statistics"]
        },
        {
            "title": "🔥 10 ADS",
            "subtitle": "10 ads",
            "price": "24 USDT",
            "save": 20,
            "badge": "Popular",
            "highlight": True,
            "features": ["AI", "Placement", "Statistics"]
        },
        {
            "title": "🔥 20 ADS",
            "subtitle": "20 ads",
            "price": "45 USDT",
            "save": 25,
            "features": ["AI", "Placement", "Statistics"]
        }
    ]
    
    # Subscription comparison
    sub_rub = [
        {
            "title": "⭐ 1 WEEK",
            "subtitle": "Unlimited",
            "price": "800 RUB",
            "features": ["AI", "Placement", "Statistics"]
        },
        {
            "title": "⭐ 1 MONTH",
            "subtitle": "Unlimited",
            "price": "2500 RUB",
            "save": 22,
            "badge": "Best Value",
            "highlight": True,
            "features": ["AI", "Placement", "Statistics"]
        },
        {
            "title": "⭐ 3 MONTHS",
            "subtitle": "Unlimited",
            "price": "6000 RUB",
            "save": 37,
            "features": ["AI", "Placement", "Statistics"]
        }
    ]
    
    sub_usd = [
        {
            "title": "⭐ 1 WEEK",
            "subtitle": "Unlimited",
            "price": "$12",
            "features": ["AI", "Placement", "Statistics"]
        },
        {
            "title": "⭐ 1 MONTH",
            "subtitle": "Unlimited",
            "price": "$37",
            "save": 22,
            "badge": "Best Value",
            "highlight": True,
            "features": ["AI", "Placement", "Statistics"]
        },
        {
            "title": "⭐ 3 MONTHS",
            "subtitle": "Unlimited",
            "price": "$90",
            "save": 37,
            "features": ["AI", "Placement", "Statistics"]
        }
    ]
    
    sub_usdt = [
        {
            "title": "⭐ 1 WEEK",
            "subtitle": "Unlimited",
            "price": "12 USDT",
            "features": ["AI", "Placement", "Statistics"]
        },
        {
            "title": "⭐ 1 MONTH",
            "subtitle": "Unlimited",
            "price": "37 USDT",
            "save": 22,
            "badge": "Best Value",
            "highlight": True,
            "features": ["AI", "Placement", "Statistics"]
        },
        {
            "title": "⭐ 3 MONTHS",
            "subtitle": "Unlimited",
            "price": "90 USDT",
            "save": 37,
            "features": ["AI", "Placement", "Statistics"]
        }
    ]
    
    # Generate
    create_comparison(onetime_rub, "One-Time Purchase", f"{OUTPUT_DIR}/comparison_onetime_RUB.png")
    create_comparison(onetime_usd, "One-Time Purchase", f"{OUTPUT_DIR}/comparison_onetime_USD.png")
    create_comparison(onetime_usdt, "One-Time Purchase", f"{OUTPUT_DIR}/comparison_onetime_USDT.png")
    
    create_comparison(sub_rub, "Subscription Plans", f"{OUTPUT_DIR}/comparison_sub_RUB.png")
    create_comparison(sub_usd, "Subscription Plans", f"{OUTPUT_DIR}/comparison_sub_USD.png")
    create_comparison(sub_usdt, "Subscription Plans", f"{OUTPUT_DIR}/comparison_sub_USDT.png")
    
    print()
    print("✅ Created 6 comparison cards")
    print(f"📁 Saved to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
