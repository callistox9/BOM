"""
Generates a sample 3-tier Azure web application architecture diagram for testing.
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1400, 900
BG = (245, 247, 250)
AZURE_BLUE = (0, 114, 198)
DARK = (30, 30, 30)
WHITE = (255, 255, 255)
LIGHT_BLUE = (213, 234, 248)
LIGHT_GREEN = (213, 245, 227)
LIGHT_ORANGE = (253, 235, 208)
LIGHT_PURPLE = (232, 218, 248)
LIGHT_RED = (253, 218, 218)
LIGHT_GREY = (230, 230, 235)
BORDER = (180, 190, 200)

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

try:
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    font_tier  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
except Exception:
    font_title = font_label = font_small = font_tier = ImageFont.load_default()


def box(x, y, w, h, fill, border=BORDER, radius=8):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=radius, fill=fill, outline=border, width=2)

def label(x, y, w, text, font, color=DARK, align="center"):
    draw.text((x + w//2, y), text, font=font, fill=color, anchor="mt")

def arrow(x1, y1, x2, y2):
    draw.line([(x1, y1), (x2, y2)], fill=(120, 130, 145), width=2)
    # arrowhead
    draw.polygon([(x2, y2), (x2-6, y2-10), (x2+6, y2-10)] if y2 > y1
                 else [(x2, y2), (x2-10, y2+6), (x2-10, y2-6)], fill=(120, 130, 145))

def harrow(x1, y1, x2, y2):
    draw.line([(x1, y1), (x2, y2)], fill=(120, 130, 145), width=2)
    draw.polygon([(x2, y2), (x2-10, y2-6), (x2-10, y2+6)], fill=(120, 130, 145))


# ── Title ────────────────────────────────────────────────────────────────────
draw.text((W//2, 18), "Azure 3-Tier Web Application Architecture", font=font_title,
          fill=AZURE_BLUE, anchor="mt")
draw.text((W//2, 48), "Region: East US  |  Availability Zone: Zone 1 & Zone 2",
          font=font_small, fill=(100, 110, 120), anchor="mt")

# ── Tier lane backgrounds ─────────────────────────────────────────────────────
TIER_Y = [75, 300, 520, 730]
tier_labels = ["Internet / Edge Layer", "Application Layer (VNet: 10.0.0.0/16)",
               "Data Layer", "Management & Security"]
tier_colors = [(230, 240, 255), (230, 250, 235), (255, 240, 225), (240, 230, 255)]

for i, (ty, tl, tc) in enumerate(zip(TIER_Y, tier_labels, tier_colors)):
    th = TIER_Y[i+1] - ty - 10 if i < len(TIER_Y)-1 else 155
    draw.rounded_rectangle([20, ty, W-20, ty+th], radius=12,
                            fill=tc, outline=BORDER, width=1)
    draw.text((38, ty+8), tl, font=font_tier, fill=(60, 60, 80))

# ── Row 1: Internet + DNS + CDN + App Gateway + WAF ──────────────────────────
# User
box(60, 110, 110, 70, LIGHT_GREY)
label(60, 115, 110, "Users /", font_label)
label(60, 133, 110, "Internet", font_label)
draw.text((115, 185), "Public", font=font_small, fill=(100,100,100), anchor="mt")

# Azure DNS
box(220, 110, 130, 70, LIGHT_BLUE)
label(220, 115, 130, "Azure DNS", font_label)
draw.text((285, 185), "Zone: example.com", font=font_small, fill=(80,80,80), anchor="mt")

# Azure CDN
box(400, 110, 130, 70, LIGHT_BLUE)
label(400, 115, 130, "Azure CDN", font_label)
draw.text((465, 185), "Standard Microsoft", font=font_small, fill=(80,80,80), anchor="mt")

# Azure Application Gateway + WAF
box(580, 100, 210, 85, LIGHT_BLUE)
label(580, 108, 210, "Azure Application", font_label)
label(580, 126, 210, "Gateway v2", font_label)
label(580, 148, 210, "+ WAF Policy", font_small, color=(80,80,80))
draw.text((685, 190), "WAF_v2 SKU  x1", font=font_small, fill=(80,80,80), anchor="mt")

# Azure Front Door
box(840, 110, 160, 70, LIGHT_BLUE)
label(840, 115, 160, "Azure Front Door", font_label)
draw.text((920, 185), "Standard Tier", font=font_small, fill=(80,80,80), anchor="mt")

# Azure Public IP
box(1060, 110, 130, 70, LIGHT_BLUE)
label(1060, 115, 130, "Public IP", font_label)
draw.text((1125, 185), "Standard SKU x2", font=font_small, fill=(80,80,80), anchor="mt")

# Row 1 arrows
harrow(170, 145, 218, 145)
harrow(350, 145, 398, 145)
harrow(530, 145, 578, 145)
harrow(790, 145, 838, 145)
harrow(1000, 145, 1058, 145)

# ── Row 2: Load Balancer + VMSS + AKS ────────────────────────────────────────
# Internal Load Balancer
box(60, 320, 160, 75, LIGHT_GREEN)
label(60, 325, 160, "Azure Load", font_label)
label(60, 343, 160, "Balancer", font_label)
draw.text((140, 400), "Standard  x1", font=font_small, fill=(80,80,80), anchor="mt")

# VM Scale Set
box(270, 315, 180, 85, LIGHT_GREEN)
label(270, 320, 180, "VM Scale Set", font_label)
label(270, 340, 180, "(Web Tier)", font_small, color=(80,80,80))
label(270, 360, 180, "Standard_D2s_v3", font_small, color=(80,80,80))
draw.text((360, 405), "Min:2  Max:10", font=font_small, fill=(80,80,80), anchor="mt")

# AKS Cluster
box(500, 315, 200, 85, LIGHT_GREEN)
label(500, 320, 200, "AKS Cluster", font_label)
label(500, 340, 200, "(App Tier)", font_small, color=(80,80,80))
label(500, 360, 200, "Standard_DS2_v2", font_small, color=(80,80,80))
draw.text((600, 405), "3 nodes  x1 cluster", font=font_small, fill=(80,80,80), anchor="mt")

# Azure Service Bus
box(750, 315, 170, 85, LIGHT_GREEN)
label(750, 325, 170, "Azure Service Bus", font_label)
label(750, 345, 170, "Namespace", font_label)
draw.text((835, 405), "Standard Tier", font=font_small, fill=(80,80,80), anchor="mt")

# Azure App Service
box(970, 315, 180, 85, LIGHT_GREEN)
label(970, 325, 180, "Azure App Service", font_label)
label(970, 345, 180, "Plan  (API)", font_label)
draw.text((1060, 405), "P2v3  x2 instances", font=font_small, fill=(80,80,80), anchor="mt")

# Azure API Management
box(1200, 315, 170, 85, LIGHT_GREEN)
label(1200, 325, 170, "API Management", font_label)
draw.text((1285, 405), "Developer Tier", font=font_small, fill=(80,80,80), anchor="mt")

# Row 2 arrows (down from App GW)
arrow(685, 185, 685, 313)
harrow(220, 357, 268, 357)
harrow(450, 357, 498, 357)
harrow(700, 357, 748, 357)
harrow(920, 357, 968, 357)
harrow(1150, 357, 1198, 357)

# ── Row 3: Data Layer ──────────────────────────────────────────────────────────
# Azure SQL DB
box(60, 545, 170, 80, LIGHT_ORANGE)
label(60, 550, 170, "Azure SQL Database", font_label)
draw.text((145, 630), "Business Critical  x1", font=font_small, fill=(80,80,80), anchor="mt")

# Azure Cosmos DB
box(280, 545, 170, 80, LIGHT_ORANGE)
label(280, 550, 170, "Azure Cosmos DB", font_label)
label(280, 568, 170, "(NoSQL)", font_small, color=(80,80,80))
draw.text((365, 630), "Serverless  x1", font=font_small, fill=(80,80,80), anchor="mt")

# Azure Cache for Redis
box(500, 545, 175, 80, LIGHT_ORANGE)
label(500, 550, 175, "Azure Cache", font_label)
label(500, 568, 175, "for Redis", font_label)
draw.text((587, 630), "C1 Standard  x1", font=font_small, fill=(80,80,80), anchor="mt")

# Azure Storage Account
box(725, 545, 175, 80, LIGHT_ORANGE)
label(725, 550, 175, "Azure Blob Storage", font_label)
draw.text((812, 630), "StorageV2 LRS  x1", font=font_small, fill=(80,80,80), anchor="mt")

# Azure Data Factory
box(950, 545, 175, 80, LIGHT_ORANGE)
label(950, 550, 175, "Azure Data Factory", font_label)
draw.text((1037, 630), "Consumption  x1", font=font_small, fill=(80,80,80), anchor="mt")

# Azure Event Hub
box(1175, 545, 175, 80, LIGHT_ORANGE)
label(1175, 550, 175, "Azure Event Hubs", font_label)
draw.text((1262, 630), "Standard  x1", font=font_small, fill=(80,80,80), anchor="mt")

# Row 3 arrows
arrow(360, 400, 145, 543)
arrow(600, 400, 590, 543)
arrow(835, 400, 812, 543)
harrow(230, 585, 278, 585)
harrow(675, 585, 723, 585)
harrow(900, 585, 948, 585)
harrow(1125, 585, 1173, 585)

# ── Row 4: Management & Security ─────────────────────────────────────────────
# Azure Key Vault
box(60, 755, 155, 70, LIGHT_PURPLE)
label(60, 760, 155, "Azure Key Vault", font_label)
draw.text((137, 830), "Standard  x1", font=font_small, fill=(80,80,80), anchor="mt")

# Azure Monitor
box(260, 755, 155, 70, LIGHT_PURPLE)
label(260, 760, 155, "Azure Monitor", font_label)
draw.text((337, 830), "+ Log Analytics", font=font_small, fill=(80,80,80), anchor="mt")

# Microsoft Defender
box(460, 755, 175, 70, LIGHT_PURPLE)
label(460, 760, 175, "Microsoft Defender", font_label)
label(460, 778, 175, "for Cloud", font_small, color=(80,80,80))

# Azure Bastion
box(685, 755, 155, 70, LIGHT_PURPLE)
label(685, 760, 155, "Azure Bastion", font_label)
draw.text((762, 830), "Standard  x1", font=font_small, fill=(80,80,80), anchor="mt")

# NSG
box(890, 755, 175, 70, LIGHT_PURPLE)
label(890, 760, 175, "Network Security", font_label)
label(890, 778, 175, "Group (NSG)  x3", font_small, color=(80,80,80))

# Azure Backup
box(1115, 755, 155, 70, LIGHT_PURPLE)
label(1115, 760, 155, "Azure Backup", font_label)
draw.text((1192, 830), "GRS Vault  x1", font=font_small, fill=(80,80,80), anchor="mt")

# Azure AD / Entra ID
box(1320, 755, 50, 70, LIGHT_PURPLE)
label(1320, 775, 50, "AAD", font_small)

# ── VNet boundary ─────────────────────────────────────────────────────────────
draw.rectangle([40, 305, W-40, 720], outline=AZURE_BLUE, width=2)
draw.text((55, 308), "Azure Virtual Network  10.0.0.0/16  (East US)", font=font_small,
          fill=AZURE_BLUE)

# Subnet labels
draw.text((55, 415), "Subnet: web-subnet 10.0.1.0/24", font=font_small, fill=(0,100,160))
draw.text((55, 640), "Subnet: data-subnet 10.0.2.0/24", font=font_small, fill=(0,100,160))


img.save("sample_azure_architecture.png", format="PNG")
print("Saved: sample_azure_architecture.png")
