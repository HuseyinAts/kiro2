# Student Dashboard Service - Mock Data Replacement Plan

**Date**: 2025-11-16
**File**: `backend/services/student_dashboard_service.py` (375 lines)
**Priority**: 🔴 CRITICAL - Highest user impact
**Estimated Time**: 4-6 hours

---

## 📊 DATABASE ANALYSIS RESULTS

### Existing Tables (Can Reuse - ✅)

| Table | Rows | Columns | Usage |
|-------|------|---------|-------|
| `exam_sessions` | 0 | 21 columns | Exam history (sinav_gecmisi) |
| `student_profiles` | 0 | 18 columns | Student profile data |
| `users` | 0 | 22 columns | User XP, level, gamification |
| `weekly_progress` | 0 | 10 columns | Performance trends |
| `student_answers` | 0 | 10 columns | Detailed question performance |

### Missing Tables (Need to Create - ❌)

| Table | Purpose | Columns Needed |
|-------|---------|----------------|
| `student_goals` | hedefler_getir() | goal_id, user_id, title, type, target_value, current_value, status, dates |
| `notifications` | bildirimler_getir() | notification_id, user_id, title, message, type, read, created_at, action_url |

---

## 🎯 IMPLEMENTATION STRATEGY

### Hybrid Approach (Recommended)

**Why Hybrid?**
- All tables are currently empty (0 rows)
- Dashboard shouldn't show completely empty screen to new users
- Need onboarding data while real data accumulates
- Production-ready behavior: show tutorials/defaults for new users

**Implementation**:
1. Create database queries for all methods
2. Add intelligent fallbacks when tables are empty
3. Show sample/onboarding data for brand new users
4. Real data overrides sample data when available

---

## 📋 DETAILED IMPLEMENTATION PLAN

### Phase 1: Create Missing Database Tables (30 min)

**File**: Create `backend/alembic/versions/xxx_add_dashboard_tables.py`

```sql
-- student_goals table
CREATE TABLE student_goals (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    goal_type VARCHAR(20) NOT NULL,  -- 'gunluk', 'haftalik', 'aylik'
    target_value FLOAT NOT NULL,
    current_value FLOAT DEFAULT 0,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    status VARCHAR(20) DEFAULT 'aktif',  -- 'aktif', 'tamamlandi', 'iptal'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- notifications table
CREATE TABLE notifications (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(20) NOT NULL,  -- 'basari', 'uyari', 'bilgi', 'hata'
    is_read BOOLEAN DEFAULT FALSE,
    action_url VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create indexes for performance
CREATE INDEX idx_student_goals_user ON student_goals(user_id);
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read);
```

### Phase 2: Replace Mock Methods with Database Queries (3 hours)

#### Method 1: `dashboard_istatistikleri_getir()` - Dashboard Statistics

**Current (Lines 33-52)**: Hardcoded fake numbers
```python
return DashboardIstatistikleri(
    tamamlanan_dersler=45,      # ❌ ALWAYS 45
    toplam_dersler=120,         # ❌ ALWAYS 120
    ortalama_puan=78.5,         # ❌ ALWAYS 78.5
)
```

**New Implementation**:
```python
async def dashboard_istatistikleri_getir(
    self, kullanici_id: str, db: Session = Depends(get_db)
) -> DashboardIstatistikleri:
    """Dashboard statistics from real database"""

    # Get user data (XP, level) from users table
    user = db.query(User).filter(User.id == kullanici_id).first()

    # Get exam statistics from exam_sessions
    completed_exams = db.query(ExamSession).filter(
        ExamSession.student_id == kullanici_id,
        ExamSession.status == 'completed'
    ).count()

    avg_score = db.query(func.avg(ExamSession.scaled_score)).filter(
        ExamSession.student_id == kullanici_id,
        ExamSession.status == 'completed'
    ).scalar() or 0.0

    # Get weekly progress from weekly_progress table
    current_week = datetime.now().isocalendar()
    week_progress = db.query(WeeklyProgress).filter(
        WeeklyProgress.user_id == kullanici_id,
        WeeklyProgress.year == current_week.year,
        WeeklyProgress.week_number == current_week.week
    ).first()

    # Calculate study time (in minutes)
    haftalik_ilerleme = (week_progress.total_time_seconds // 60) if week_progress else 0

    # Return real data with intelligent defaults for new users
    return DashboardIstatistikleri(
        tamamlanan_dersler=0,  # TODO: Implement lesson tracking
        toplam_dersler=120,    # Default curriculum
        tamamlanan_sinavlar=completed_exams,
        ortalama_puan=float(avg_score),
        toplam_calisma_suresi=haftalik_ilerleme,  # This week
        haftalik_hedef=300,  # Default 5 hours/week
        haftalik_ilerleme=haftalik_ilerleme,
        gunluk_seri=week_progress.streak_days if week_progress else 0,
        toplam_puan=user.total_xp if user else 0,
        seviye=user.level if user else 1,
        deneyim=user.total_xp if user else 0,
        sonraki_seviye_deneyim=(user.level + 1) * 1000 if user else 1000,
    )
```

---

#### Method 2: `sinav_gecmisi_getir()` - Exam History

**Current (Lines 54-118)**: 3 hardcoded fake exams
```python
mock_sinavlar = [
    SinavSonucu(sinav_id="sinav_001", sinav_adi="TYT Deneme 1", ...),  # ❌ FAKE
]
```

**New Implementation**:
```python
async def sinav_gecmisi_getir(
    self,
    kullanici_id: str,
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
    sinav_tipi: Optional[str] = None,
) -> List[SinavSonucu]:
    """Real exam history from exam_sessions table"""

    query = db.query(ExamSession).filter(
        ExamSession.student_id == kullanici_id,
        ExamSession.status == 'completed'
    )

    # Filter by exam type if specified
    if sinav_tipi:
        query = query.filter(ExamSession.exam_type == sinav_tipi)

    # Order by most recent first, with pagination
    exams = query.order_by(ExamSession.completed_at.desc()).offset(offset).limit(limit).all()

    # Convert to SinavSonucu format
    sinavlar = []
    for exam in exams:
        # Get topic performance from student_answers
        topic_performance = self._calculate_topic_performance(exam.id, db)

        sinavlar.append(
            SinavSonucu(
                sinav_id=exam.id,
                sinav_adi=exam.exam_name,
                sinav_tipi=exam.exam_type,
                tarih=exam.completed_at,
                puan=float(exam.scaled_score or 0),
                dogru_sayisi=exam.total_correct,
                yanlis_sayisi=exam.total_wrong,
                bos_sayisi=exam.total_empty,
                sure=exam.duration_minutes,
                konu_performanslari=topic_performance,
            )
        )

    # If no exams found, return empty list (NOT fake data)
    return sinavlar

def _calculate_topic_performance(self, exam_session_id: str, db: Session) -> Dict[str, float]:
    """Calculate topic-wise performance from student_answers"""
    # Query student_answers joined with questions to get topics
    # This is a helper method to avoid mock data
    # TODO: Implement when question-topic mapping is added
    return {}
```

---

#### Method 3: `performans_trendi_getir()` - Performance Trends

**Current (Lines 120-143)**: Random fake data with `random.randint()`!
```python
import random
performans_verisi.append(
    PerformansVerisi(
        puan=random.randint(50, 200),  # ❌ CHANGES ON EVERY PAGE RELOAD!
    )
)
```

**New Implementation**:
```python
async def performans_trendi_getir(
    self, kullanici_id: str, db: Session = Depends(get_db), gun_sayisi: int = 30
) -> List[PerformansVerisi]:
    """Real performance trends from weekly_progress and exam_sessions"""

    # Get last N days of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=gun_sayisi)

    # Query exam_sessions grouped by date
    daily_exams = db.query(
        func.date(ExamSession.completed_at).label('date'),
        func.count(ExamSession.id).label('exam_count'),
        func.avg(ExamSession.scaled_score).label('avg_score')
    ).filter(
        ExamSession.student_id == kullanici_id,
        ExamSession.completed_at >= start_date,
        ExamSession.status == 'completed'
    ).group_by(func.date(ExamSession.completed_at)).all()

    # Convert to daily performance data
    performans_verisi = []
    exam_dict = {str(e.date): e for e in daily_exams}

    for i in range(gun_sayisi):
        tarih = start_date + timedelta(days=i)
        tarih_str = tarih.strftime('%Y-%m-%d')

        exam_data = exam_dict.get(tarih_str)

        performans_verisi.append(
            PerformansVerisi(
                tarih=tarih_str,
                dersler=0,  # TODO: Implement lesson tracking
                sinavlar=exam_data.exam_count if exam_data else 0,
                puan=int(exam_data.avg_score or 0) if exam_data else 0,
                calisma_suresi=0,  # TODO: Get from weekly_progress daily_data JSON
            )
        )

    return performans_verisi
```

---

#### Method 4: `hedefler_getir()` - Goals

**Current (Lines 145-190)**: 3 hardcoded fake goals
```python
mock_hedefler = [
    Hedef(hedef_id="hedef_001", baslik="Günlük 2 Saat Çalışma", ...),  # ❌ FAKE
]
```

**New Implementation**:
```python
async def hedefler_getir(
    self, kullanici_id: str, db: Session = Depends(get_db), aktif_sadece: bool = False
) -> List[Hedef]:
    """Real goals from student_goals table"""

    query = db.query(StudentGoal).filter(StudentGoal.user_id == kullanici_id)

    if aktif_sadece:
        query = query.filter(StudentGoal.status == 'aktif')

    goals = query.order_by(StudentGoal.created_at.desc()).all()

    # Convert to Hedef format
    hedefler = []
    for goal in goals:
        hedefler.append(
            Hedef(
                hedef_id=goal.id,
                baslik=goal.title,
                aciklama=goal.description,
                hedef_tipi=goal.goal_type,
                hedef_degeri=goal.target_value,
                mevcut_deger=goal.current_value,
                baslangic_tarihi=goal.start_date,
                bitis_tarihi=goal.end_date,
                durum=goal.status,
                olusturma_tarihi=goal.created_at,
            )
        )

    # If new user with no goals, create default onboarding goal
    if not hedefler:
        default_goal = await self._create_default_goal(kullanici_id, db)
        if default_goal:
            hedefler.append(default_goal)

    return hedefler

async def _create_default_goal(self, kullanici_id: str, db: Session) -> Optional[Hedef]:
    """Create default onboarding goal for new users"""
    # Create a "Complete first exam" goal
    # This ensures new users have something to work towards
    # TODO: Implement auto-goal creation
    return None
```

---

#### Method 5: `bildirimler_getir()` - Notifications

**Current (Lines 222-261)**: 3 hardcoded fake notifications
```python
mock_bildirimler = [
    Bildirim(bildirim_id="bildirim_001", baslik="Tebrikler!", ...),  # ❌ FAKE
]
```

**New Implementation**:
```python
async def bildirimler_getir(
    self, kullanici_id: str, db: Session = Depends(get_db),
    okunmamis_sadece: bool = False, limit: int = 50
) -> List[Bildirim]:
    """Real notifications from notifications table"""

    query = db.query(Notification).filter(Notification.user_id == kullanici_id)

    if okunmamis_sadece:
        query = query.filter(Notification.is_read == False)

    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()

    # Convert to Bildirim format
    bildirimler = []
    for notif in notifications:
        bildirimler.append(
            Bildirim(
                bildirim_id=notif.id,
                baslik=notif.title,
                mesaj=notif.message,
                tip=notif.notification_type,
                okundu=notif.is_read,
                tarih=notif.created_at,
                eylem_url=notif.action_url,
            )
        )

    # If new user, create welcome notification
    if not notifications:
        welcome_notif = await self._create_welcome_notification(kullanici_id, db)
        if welcome_notif:
            bildirimler.append(welcome_notif)

    return bildirimler
```

---

#### Method 6: `ogrenci_profili_getir()` - Student Profile

**Current (Lines 271-295)**: Hardcoded fake profile
```python
return OgrenciProfili(
    sinif_seviyesi=12,                    # ❌ ALWAYS 12
    okul_adi="Atatürk Anadolu Lisesi",    # ❌ ALWAYS same school
)
```

**New Implementation**:
```python
async def ogrenci_profili_getir(
    self, kullanici_id: str, db: Session = Depends(get_db)
) -> Optional[OgrenciProfili]:
    """Real student profile from student_profiles table"""

    # Get student profile
    profile = db.query(StudentProfile).filter(
        StudentProfile.user_id == kullanici_id
    ).first()

    if not profile:
        # Profile doesn't exist - create default
        return await self._create_default_profile(kullanici_id, db)

    # Get user data for additional info
    user = db.query(User).filter(User.id == kullanici_id).first()

    return OgrenciProfili(
        ogrenci_id=profile.id,
        kullanici_id=kullanici_id,
        sinif_seviyesi=profile.grade_level,
        okul_adi=profile.school_name or "Okul belirtilmedi",
        hedef_sinav="TYT",  # Default, should be from profile
        hedef_universiteler=[profile.target_university] if profile.target_university else [],
        ogrenme_stili=profile.learning_style or "gorsel",
        guclu_alanlar=[],  # TODO: Calculate from performance data
        zayif_alanlar=[],  # TODO: Calculate from performance data
        gunluk_calisma_hedefi=profile.study_hours_per_day or 120,
        veli_onay=True,  # Default
        olusturma_tarihi=profile.created_at,
        son_guncelleme=profile.updated_at,
    )
```

---

### Phase 3: Remove Mock Data Storage (15 min)

**Delete Lines 23-31**:
```python
# DELETE THIS ENTIRE SECTION
self.mock_data = {
    "istatistikler": {},
    "sinav_gecmisi": {},
    "hedefler": {},
    "bildirimler": {},
    "performans_verisi": {},
    "profiller": {},
}
```

**Delete all references to `self.mock_data` throughout the file**:
- Line 200-203: `self.mock_data["hedefler"]` usage
- Line 325: `self.mock_data["profiller"]` usage

---

### Phase 4: Add Database Session Dependency (30 min)

**Update service initialization**:
```python
# OLD: __init__ with no dependencies
def __init__(self):
    self.mock_data = {...}

# NEW: No __init__ needed, use dependency injection
# All methods now have db: Session = Depends(get_db) parameter
```

**Add to imports**:
```python
from fastapi import Depends
from sqlalchemy.orm import Session
from core.database import get_db
from models.user import User
from models.student_profile import StudentProfile
from models.exam_session import ExamSession
from models.weekly_progress import WeeklyProgress
from models.student_goal import StudentGoal  # New model
from models.notification import Notification  # New model
```

---

### Phase 5: Create SQLAlchemy Models for New Tables (30 min)

**File**: `backend/models/student_goal.py` (NEW)
```python
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from core.database import Base

class StudentGoal(Base):
    __tablename__ = "student_goals"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String)
    goal_type = Column(String(20), nullable=False)
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, default=0)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(String(20), default="aktif")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

**File**: `backend/models/notification.py` (NEW)
```python
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from core.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(String, nullable=False)
    notification_type = Column(String(20), nullable=False)
    is_read = Column(Boolean, default=False)
    action_url = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())
```

---

## 🎯 TESTING PLAN

### Unit Tests
```python
# test_dashboard_service_db.py

async def test_dashboard_stats_with_real_db():
    """Test dashboard stats query real database"""
    service = OgrenciDashboardServisi()
    stats = await service.dashboard_istatistikleri_getir("test_user_123", db=test_db)

    # Should return real data, not hardcoded 45/120
    assert stats.tamamlanan_dersler >= 0  # Real count
    assert stats.tamamlanan_sinavlar >= 0  # From exam_sessions

async def test_exam_history_empty_returns_empty_list():
    """Test exam history returns [] when no exams, not fake data"""
    service = OgrenciDashboardServisi()
    history = await service.sinav_gecmisi_getir("new_user", db=test_db)

    assert history == []  # Not 3 fake exams!
```

### Integration Tests
```python
async def test_full_dashboard_workflow():
    """Test complete dashboard with real database"""
    # 1. Create user
    user = create_test_user(db)

    # 2. Create exam session
    exam = create_test_exam_session(user.id, db)

    # 3. Get dashboard data
    service = OgrenciDashboardServisi()
    stats = await service.dashboard_istatistikleri_getir(user.id, db)

    # 4. Verify real data
    assert stats.tamamlanan_sinavlar == 1  # Real count
    assert stats.toplam_puan == user.total_xp  # From users table
```

---

## ✅ SUCCESS CRITERIA

### Before (Current State)
```python
# Returns same fake data for ALL users
dashboard_istatistikleri_getir("user_1") == dashboard_istatistikleri_getir("user_2")  # ❌ TRUE!

# Random data changes on reload
performans_trendi_getir("user_1")[0].puan != performans_trendi_getir("user_1")[0].puan  # ❌ TRUE!
```

### After (Target State)
```python
# Returns unique data per user
dashboard_istatistikleri_getir("user_1") != dashboard_istatistikleri_getir("user_2")  # ✅

# Consistent data on reload
performans_trendi_getir("user_1") == performans_trendi_getir("user_1")  # ✅

# Empty tables return empty/default data
sinav_gecmisi_getir("new_user") == []  # ✅ Not fake exams

# self.mock_data removed completely
grep -r "self.mock_data" student_dashboard_service.py  # ✅ No matches
```

---

## 📅 TIMELINE

| Phase | Task | Duration | Status |
|-------|------|----------|--------|
| 1 | Create database tables | 30 min | ⏳ Pending |
| 2.1 | Replace dashboard_istatistikleri_getir | 30 min | ⏳ Pending |
| 2.2 | Replace sinav_gecmisi_getir | 45 min | ⏳ Pending |
| 2.3 | Replace performans_trendi_getir | 30 min | ⏳ Pending |
| 2.4 | Replace hedefler_getir | 30 min | ⏳ Pending |
| 2.5 | Replace bildirimler_getir | 30 min | ⏳ Pending |
| 2.6 | Replace ogrenci_profili_getir | 15 min | ⏳ Pending |
| 3 | Remove self.mock_data | 15 min | ⏳ Pending |
| 4 | Add dependency injection | 30 min | ⏳ Pending |
| 5 | Create SQLAlchemy models | 30 min | ⏳ Pending |
| 6 | Write tests | 45 min | ⏳ Pending |
| 7 | Integration testing | 30 min | ⏳ Pending |
| **TOTAL** | | **5 hours 30 minutes** | ⏳ Pending |

---

## 🚀 READY TO BEGIN

**Next Command**: Create Alembic migration for new tables

**Status**: ✅ Analysis complete, ready to implement
**Blocker**: None
**Risk**: Low - incremental replacement with rollback capability
