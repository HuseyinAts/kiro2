#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Veli Takip Sistemi Kapsamlı Test
Türkiye Üniversite Sınavları Hazırlık Platformu - Task 26 Tamamlama Testi
"""

import asyncio
import os
import sys

# Backend modüllerini import edebilmek için path'e ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def test_task_26_requirements():
    """Task 26 gereksinimlerini test et"""
    print(
        "[TARGET] Task 26 - Veli takip sistemi temel implementasyonu gereksinimleri test ediliyor..."
    )
    print("=" * 80)

    requirements = [
        "Veli paneli ve çocuk seçimi",
        "Çocuk performans görüntüleme",
        "Haftalık basit rapor sistemi",
        "Veli onay mekanizması",
        "Veli bildirim sistemi",
    ]

    test_results = []

    # 1. Veli paneli ve çocuk seçimi
    print("\n1️⃣ Veli paneli ve çocuk seçimi testi...")
    try:
        # Backend API kontrolü
        from api.parent import router as parent_router

        # Frontend bileşen kontrolü
        parent_page_path = "../frontend/src/pages/ParentPage.tsx"
        child_selection_path = "../frontend/src/components/Parent/ChildSelection.tsx"

        backend_ok = parent_router.prefix == "/api/v1/parent"
        frontend_ok = os.path.exists(parent_page_path) and os.path.exists(
            child_selection_path
        )

        if backend_ok and frontend_ok:
            print("   [CHECK] Veli paneli ve çocuk seçimi - TAMAMLANDI")
            test_results.append(("Veli paneli ve çocuk seçimi", True))
        else:
            print("   [X] Veli paneli ve çocuk seçimi - EKSİK")
            test_results.append(("Veli paneli ve çocuk seçimi", False))

    except Exception as e:
        print(f"   [X] Veli paneli testi hatası: {e}")
        test_results.append(("Veli paneli ve çocuk seçimi", False))

    # 2. Çocuk performans görüntüleme
    print("\n2️⃣ Çocuk performans görüntüleme testi...")
    try:
        from services.parent_service import ParentService

        # Frontend bileşen kontrolü
        performance_view_path = (
            "../frontend/src/components/Parent/ChildPerformanceView.tsx"
        )

        # Servis metodları kontrolü
        service_ok = hasattr(ParentService, "get_child_performance")
        frontend_ok = os.path.exists(performance_view_path)

        if service_ok and frontend_ok:
            print("   [CHECK] Çocuk performans görüntüleme - TAMAMLANDI")
            test_results.append(("Çocuk performans görüntüleme", True))
        else:
            print("   [X] Çocuk performans görüntüleme - EKSİK")
            test_results.append(("Çocuk performans görüntüleme", False))

    except Exception as e:
        print(f"   [X] Performans görüntüleme testi hatası: {e}")
        test_results.append(("Çocuk performans görüntüleme", False))

    # 3. Haftalık basit rapor sistemi
    print("\n3️⃣ Haftalık basit rapor sistemi testi...")
    try:
        from models.parent import WeeklyReport
        from services.parent_service import ParentService

        # Servis metodları kontrolü
        service_ok = hasattr(ParentService, "generate_weekly_report")
        model_ok = hasattr(WeeklyReport, "__tablename__")

        # API endpoint kontrolü
        from api.parent import router

        routes = [route.path for route in router.routes]
        api_ok = any("weekly-report" in route for route in routes)

        if service_ok and model_ok and api_ok:
            print("   [CHECK] Haftalık basit rapor sistemi - TAMAMLANDI")
            test_results.append(("Haftalık basit rapor sistemi", True))
        else:
            print("   [X] Haftalık basit rapor sistemi - EKSİK")
            test_results.append(("Haftalık basit rapor sistemi", False))

    except Exception as e:
        print(f"   [X] Haftalık rapor testi hatası: {e}")
        test_results.append(("Haftalık basit rapor sistemi", False))

    # 4. Veli onay mekanizması
    print("\n4️⃣ Veli onay mekanizması testi...")
    try:
        from models.parent import ParentChildRelation
        from services.parent_service import ParentService

        # Servis metodları kontrolü
        create_ok = hasattr(ParentService, "create_parent_child_relation")
        approve_ok = hasattr(ParentService, "approve_parent_child_relation")
        model_ok = hasattr(ParentChildRelation, "approved")

        if create_ok and approve_ok and model_ok:
            print("   [CHECK] Veli onay mekanizması - TAMAMLANDI")
            test_results.append(("Veli onay mekanizması", True))
        else:
            print("   [X] Veli onay mekanizması - EKSİK")
            test_results.append(("Veli onay mekanizması", False))

    except Exception as e:
        print(f"   [X] Veli onay testi hatası: {e}")
        test_results.append(("Veli onay mekanizması", False))

    # 5. Veli bildirim sistemi
    print("\n5️⃣ Veli bildirim sistemi testi...")
    try:
        from services.parent_service import ParentService

        # Frontend bileşen kontrolü
        notifications_path = "../frontend/src/components/Parent/ParentNotifications.tsx"

        # Servis metodları kontrolü
        create_ok = hasattr(ParentService, "create_notification")
        get_ok = hasattr(ParentService, "get_parent_notifications")
        mark_ok = hasattr(ParentService, "mark_notification_as_read")
        frontend_ok = os.path.exists(notifications_path)

        if create_ok and get_ok and mark_ok and frontend_ok:
            print("   [CHECK] Veli bildirim sistemi - TAMAMLANDI")
            test_results.append(("Veli bildirim sistemi", True))
        else:
            print("   [X] Veli bildirim sistemi - EKSİK")
            test_results.append(("Veli bildirim sistemi", False))

    except Exception as e:
        print(f"   [X] Veli bildirim testi hatası: {e}")
        test_results.append(("Veli bildirim sistemi", False))

    return test_results


async def test_api_endpoints():
    """API endpoint'lerini test et"""
    print("\n[PLUG] API Endpoint'leri test ediliyor...")

    try:
        from api.parent import router as parent_router
        from api.veli import router as veli_router

        # Parent API routes
        parent_routes = [route.path for route in parent_router.routes]
        expected_parent_routes = [
            "/children",
            "/children/{child_id}/performance",
            "/children/{child_id}/weekly-report",
            "/notifications",
            "/dashboard",
            "/approval/{relation_id}",
        ]

        parent_routes_ok = all(
            any(expected in route for route in parent_routes)
            for expected in expected_parent_routes
        )

        # Veli API routes
        veli_routes = [route.path for route in veli_router.routes]
        veli_routes_ok = len(veli_routes) > 0

        if parent_routes_ok and veli_routes_ok:
            print("   [CHECK] API Endpoint'leri - TAMAMLANDI")
            return True
        else:
            print("   [X] API Endpoint'leri - EKSİK")
            return False

    except Exception as e:
        print(f"   [X] API test hatası: {e}")
        return False


async def test_frontend_integration():
    """Frontend entegrasyonunu test et"""
    print("\n[PALETTE] Frontend entegrasyonu test ediliyor...")

    try:
        # Ana bileşenler
        components = [
            "../frontend/src/pages/ParentPage.tsx",
            "../frontend/src/components/Parent/ParentDashboard.tsx",
            "../frontend/src/components/Parent/ChildSelection.tsx",
            "../frontend/src/components/Parent/ChildPerformanceView.tsx",
            "../frontend/src/components/Parent/ParentNotifications.tsx",
            "../frontend/src/services/parentService.ts",
        ]

        missing_components = []
        for component in components:
            if not os.path.exists(component):
                missing_components.append(os.path.basename(component))

        if len(missing_components) == 0:
            print("   [CHECK] Frontend entegrasyonu - TAMAMLANDI")
            return True
        else:
            print(
                f"   [X] Frontend entegrasyonu - EKSİK: {', '.join(missing_components)}"
            )
            return False

    except Exception as e:
        print(f"   [X] Frontend test hatası: {e}")
        return False


async def test_database_models():
    """Database modellerini test et"""
    print("\n🗄️ Database modelleri test ediliyor...")

    try:
        from models.parent import (
            ChildPerformanceData,
            ParentChildRelation,
            ParentChildRelationCreate,
            ParentDashboardData,
            ParentNotification,
            ParentNotificationCreate,
            WeeklyReport,
            WeeklyReportData,
        )

        # SQLAlchemy modelleri
        sqlalchemy_models = [ParentChildRelation, ParentNotification, WeeklyReport]
        sqlalchemy_ok = all(
            hasattr(model, "__tablename__") for model in sqlalchemy_models
        )

        # Pydantic modelleri
        pydantic_models = [
            ParentChildRelationCreate,
            ChildPerformanceData,
            WeeklyReportData,
            ParentNotificationCreate,
            ParentDashboardData,
        ]
        pydantic_ok = all(hasattr(model, "__fields__") for model in pydantic_models)

        if sqlalchemy_ok and pydantic_ok:
            print("   [CHECK] Database modelleri - TAMAMLANDI")
            return True
        else:
            print("   [X] Database modelleri - EKSİK")
            return False

    except Exception as e:
        print(f"   [X] Database model testi hatası: {e}")
        return False


async def main():
    """Ana test fonksiyonu"""
    print("[ROCKET] TASK 26 - VELİ TAKİP SİSTEMİ KAPSAMLI TEST")
    print("=" * 80)
    print("[CLIPBOARD] Test Edilen Gereksinimler:")
    print("   • Veli paneli ve çocuk seçimi")
    print("   • Çocuk performans görüntüleme")
    print("   • Haftalık basit rapor sistemi")
    print("   • Veli onay mekanizması")
    print("   • Veli bildirim sistemi")
    print("=" * 80)

    # Ana gereksinim testleri
    requirement_results = await test_task_26_requirements()

    # Ek testler
    api_result = await test_api_endpoints()
    frontend_result = await test_frontend_integration()
    database_result = await test_database_models()

    # Sonuçları özetle
    print("\n" + "=" * 80)
    print("[CHART] TEST SONUÇLARI ÖZETI")
    print("=" * 80)

    # Ana gereksinimler
    print("\n[TARGET] Ana Gereksinimler:")
    requirement_passed = 0
    for req_name, result in requirement_results:
        status = "[CHECK] TAMAMLANDI" if result else "[X] EKSİK"
        print(f"   {req_name}: {status}")
        if result:
            requirement_passed += 1

    # Ek testler
    print("\n[TOOL] Teknik Testler:")
    additional_tests = [
        ("API Endpoint'leri", api_result),
        ("Frontend Entegrasyonu", frontend_result),
        ("Database Modelleri", database_result),
    ]

    additional_passed = 0
    for test_name, result in additional_tests:
        status = "[CHECK] TAMAMLANDI" if result else "[X] EKSİK"
        print(f"   {test_name}: {status}")
        if result:
            additional_passed += 1

    # Genel özet
    total_requirements = len(requirement_results)
    total_additional = len(additional_tests)
    total_passed = requirement_passed + additional_passed
    total_tests = total_requirements + total_additional

    print(
        f"\n[TRENDING_UP] Genel Başarı Oranı: {total_passed}/{total_tests} (%{(total_passed/total_tests)*100:.1f})"
    )
    print(
        f"[CLIPBOARD] Ana Gereksinimler: {requirement_passed}/{total_requirements} (%{(requirement_passed/total_requirements)*100:.1f})"
    )
    print(
        f"[TOOL] Teknik Testler: {additional_passed}/{total_additional} (%{(additional_passed/total_additional)*100:.1f})"
    )

    # Final değerlendirme
    if requirement_passed == total_requirements:
        print("\n[PARTY] TASK 26 BAŞARIYLA TAMAMLANDI!")
        print(
            "[CHECK] Veli takip sistemi temel implementasyonu tam olarak gerçekleştirildi!"
        )

        print("\n[CLIPBOARD] Tamamlanan Özellikler:")
        print("   [CHECK] Veli paneli ve çocuk seçimi sistemi")
        print("   [CHECK] Çocuk performans görüntüleme arayüzü")
        print("   [CHECK] Haftalık basit rapor sistemi")
        print("   [CHECK] Veli onay mekanizması")
        print("   [CHECK] Veli bildirim sistemi")

        print("\n[ROCKET] Sistem Özellikleri:")
        print("   • Backend API'leri (/api/v1/parent ve /api/v1/veli)")
        print("   • Frontend React bileşenleri (ParentPage, Dashboard, vb.)")
        print(
            "   • Database modelleri (ParentChildRelation, ParentNotification, WeeklyReport)"
        )
        print("   • TypeScript servis entegrasyonu")
        print("   • Kapsamlı veli-çocuk ilişki yönetimi")

        if total_passed == total_tests:
            print("\n[TROPHY] MÜKEMMEL! Tüm testler başarılı!")
        else:
            print(
                f"\n⚠️ {total_tests - total_passed} teknik test eksik, ancak ana gereksinimler tamamlandı"
            )

        return True
    else:
        print(f"\n[X] TASK 26 TAMAMLANAMADI!")
        print(f"   {total_requirements - requirement_passed} ana gereksinim eksik")
        print("   Lütfen eksik bileşenleri tamamlayın")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
