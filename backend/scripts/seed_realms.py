"""
12 YKS Alemi ve varsayilan rozetler seed script.

FAZ-2 Gorev 2.2 — Master Plan v2.0
Calistir: python scripts/seed_realms.py
"""

import os
import sys

# Backend root'u path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json

import psycopg2

DB_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5434/kiro2"
)

REALMS = [
    {
        "slug": "fizik",
        "name": "Fizik Alemi",
        "era": "Miryakefalon Kalesi, 1176",
        "npc_name": "Cevheri Bey",
        "npc_title": "Enerji Ustasi",
        "tech_stack": ["threejs", "matterjs"],
        "color_primary": "#6C5CE7",
        "color_secondary": "#A29BFE",
        "order_index": 1,
    },
    {
        "slug": "kimya",
        "name": "Kimya Alemi",
        "era": "Beyt'ul Hikme, 850",
        "npc_name": "El-Kindi",
        "npc_title": "Simyager",
        "tech_stack": ["threejs", "vsupr"],
        "color_primary": "#00B4D8",
        "color_secondary": "#90E0EF",
        "order_index": 2,
    },
    {
        "slug": "biyoloji",
        "name": "Biyoloji Alemi",
        "era": "Goktork Yurdu, 570",
        "npc_name": "Tbc Ana",
        "npc_title": "Yasam Rehberi",
        "tech_stack": ["threejs"],
        "color_primary": "#00B894",
        "color_secondary": "#55EFC4",
        "order_index": 3,
    },
    {
        "slug": "matematik",
        "name": "Matematik Alemi",
        "era": "Harezm, 780",
        "npc_name": "El-Harezmi",
        "npc_title": "Sayi Bilgesi",
        "tech_stack": ["threejs", "p5js"],
        "color_primary": "#2D7CF6",
        "color_secondary": "#74B9FF",
        "order_index": 4,
    },
    {
        "slug": "geometri",
        "name": "Geometri Alemi",
        "era": "Sulemaniye, 1550",
        "npc_name": "Mimar Sinan",
        "npc_title": "Form Ustasi",
        "tech_stack": ["threejs", "csg"],
        "color_primary": "#A74BFF",
        "color_secondary": "#DFE6E9",
        "order_index": 5,
    },
    {
        "slug": "cografya",
        "name": "Cografya Alemi",
        "era": "Kasgar, 1072",
        "npc_name": "Kasgari Mahmud",
        "npc_title": "Haritaci",
        "tech_stack": ["d3", "cesiumjs"],
        "color_primary": "#6AB04C",
        "color_secondary": "#BADC58",
        "order_index": 6,
    },
    {
        "slug": "tarih",
        "name": "Tarih Alemi",
        "era": "Ankara, 1920",
        "npc_name": "Kurmay Subay",
        "npc_title": "Tarihci",
        "tech_stack": ["d3"],
        "color_primary": "#F0932B",
        "color_secondary": "#F9CA24",
        "order_index": 7,
    },
    {
        "slug": "edebiyat",
        "name": "Edebiyat Alemi",
        "era": "Anadolu, 1310",
        "npc_name": "Yunus Emre",
        "npc_title": "Ozan",
        "tech_stack": ["d3", "nlp"],
        "color_primary": "#A8235B",
        "color_secondary": "#E17055",
        "order_index": 8,
    },
    {
        "slug": "turkce",
        "name": "Turkce Alemi",
        "era": "Kasgar, 1072",
        "npc_name": "Dilmac",
        "npc_title": "Dil Ustasi",
        "tech_stack": ["interactive"],
        "color_primary": "#E17055",
        "color_secondary": "#FAB1A0",
        "order_index": 9,
    },
    {
        "slug": "felsefe",
        "name": "Felsefe Alemi",
        "era": "Buhara, 980",
        "npc_name": "Ibn-i Sina",
        "npc_title": "Hakim",
        "tech_stack": ["d3"],
        "color_primary": "#A29BFF",
        "color_secondary": "#DFE6E9",
        "order_index": 10,
    },
    {
        "slug": "din",
        "name": "Din Kulturu",
        "era": "Medrese, 1200",
        "npc_name": "Mudurris",
        "npc_title": "Alim",
        "tech_stack": ["2d"],
        "color_primary": "#FDCB6E",
        "color_secondary": "#FFF3CD",
        "order_index": 11,
    },
    {
        "slug": "oba",
        "name": "Oba Merkezi",
        "era": "Ergenekon, Efsanevi",
        "npc_name": "Bilge Alp",
        "npc_title": "Yol Gosterici",
        "tech_stack": ["lottie", "llm"],
        "color_primary": "#534A87",
        "color_secondary": "#A29BFE",
        "order_index": 12,
    },
]

DEFAULT_BADGES = [
    {
        "slug": "ilk_adim",
        "name": "Ilk Adim",
        "description": "Ilk soruyu dogru cevapla",
        "icon": "🎯",
        "category": "katilim",
        "condition": {"type": "first_correct"},
    },
    {
        "slug": "yedi_gun",
        "name": "Haftalik Guclu",
        "description": "7 gunluk streak yap",
        "icon": "🔥",
        "category": "streak",
        "condition": {"type": "streak", "value": 7},
    },
    {
        "slug": "usta_fizik",
        "name": "Fizik Ustasi",
        "description": "Fizik Alemi'nde ustalastin",
        "icon": "⚡",
        "category": "basari",
        "condition": {"type": "realm_mastery", "realm": "fizik"},
    },
    {
        "slug": "duel_kazanan",
        "name": "Duello Sampiyonu",
        "description": "Ilk duelloyu kazan",
        "icon": "⚔️",
        "category": "sosyal",
        "condition": {"type": "duel_win", "value": 1},
    },
    {
        "slug": "yz_soru",
        "name": "100 Soru",
        "description": "100 soru cevapla",
        "icon": "💯",
        "category": "beceri",
        "condition": {"type": "questions_answered", "value": 100},
    },
]


def seed():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        # Realms
        realm_count = 0
        for r in REALMS:
            cur.execute(
                """
                INSERT INTO realms (slug, name, era, npc_name, npc_title,
                    tech_stack, color_primary, color_secondary, order_index, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, true)
                ON CONFLICT (slug) DO UPDATE SET
                    name=EXCLUDED.name,
                    era=EXCLUDED.era,
                    npc_name=EXCLUDED.npc_name,
                    npc_title=EXCLUDED.npc_title,
                    tech_stack=EXCLUDED.tech_stack,
                    color_primary=EXCLUDED.color_primary,
                    color_secondary=EXCLUDED.color_secondary,
                    order_index=EXCLUDED.order_index
                """,
                (
                    r["slug"],
                    r["name"],
                    r["era"],
                    r["npc_name"],
                    r["npc_title"],
                    json.dumps(r["tech_stack"]),
                    r.get("color_primary"),
                    r.get("color_secondary"),
                    r["order_index"],
                ),
            )
            realm_count += 1

        # Badges
        badge_count = 0
        for b in DEFAULT_BADGES:
            cur.execute(
                """
                INSERT INTO badges (slug, name, description, icon, category, condition)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (slug) DO UPDATE SET
                    name=EXCLUDED.name,
                    description=EXCLUDED.description,
                    icon=EXCLUDED.icon,
                    category=EXCLUDED.category,
                    condition=EXCLUDED.condition
                """,
                (
                    b["slug"],
                    b["name"],
                    b["description"],
                    b["icon"],
                    b["category"],
                    json.dumps(b["condition"]),
                ),
            )
            badge_count += 1

        conn.commit()
        print(f"OK: {realm_count} alem, {badge_count} rozet eklendi/guncellendi.")
        conn.close()

    except Exception as e:
        print(f"HATA: {e}")
        sys.exit(1)


if __name__ == "__main__":
    seed()
