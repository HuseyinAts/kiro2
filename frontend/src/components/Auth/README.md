# Role-Based Access Control (RBAC) Sistemi

Bu klasör, EğitimEylemci platformu için kapsamlı bir Role-Based Access Control (RBAC) sistemi içerir.

## 🎯 Özellikler

### ✅ Tamamlanan Özellikler

#### 1. Rol Yönetimi
- **4 Ana Rol**: Öğrenci, Öğretmen, Veli, Admin
- **Rol Bazlı Dashboard'lar**: Her rol için özel dashboard
- **Rol Bazlı Navigation**: Dinamik menü sistemi
- **Rol Kontrolü**: Sayfa ve bileşen seviyesinde

#### 2. İzin Sistemi
- **Granular İzinler**: Resource ve action bazlı izin kontrolü
- **Rol Bazlı İzinler**: Her rol için önceden tanımlı izin setleri
- **Dinamik İzin Kontrolü**: Runtime'da izin doğrulama

#### 3. Authentication & Authorization
- **JWT Token Yönetimi**: Access ve refresh token sistemi
- **Otomatik Token Yenileme**: Seamless kullanıcı deneyimi
- **Session Yönetimi**: Güvenli oturum kontrolü
- **Protected Routes**: Korumalı sayfa erişimi

#### 4. UI Bileşenleri
- **ProtectedRoute**: Sayfa seviyesi koruma
- **RoleBasedComponent**: Bileşen seviyesi koruma
- **Role-Specific Components**: Her rol için özel UI bileşenleri
- **Unauthorized Handling**: Yetkisiz erişim yönetimi

## 📁 Dosya Yapısı

```
frontend/src/
├── components/
│   ├── Auth/
│   │   ├── ProtectedRoute.tsx          # Korumalı route bileşeni
│   │   └── README.md                   # Bu dosya
│   ├── Common/
│   │   └── RoleBasedComponent.tsx      # Rol bazlı bileşen wrapper
│   ├── Layout/
│   │   └── RoleBasedLayout.tsx         # Rol bazlı layout
│   ├── Navigation/
│   │   └── RoleBasedNavigation.tsx     # Dinamik navigasyon
│   └── RoleSpecific/
│       ├── StudentComponents.tsx       # Öğrenci bileşenleri
│       ├── TeacherComponents.tsx       # Öğretmen bileşenleri
│       ├── ParentComponents.tsx        # Veli bileşenleri
│       ├── AdminComponents.tsx         # Admin bileşenleri
│       └── index.ts                    # Export dosyası
├── hooks/
│   ├── useAuth.ts                      # Authentication hook
│   └── useRoleAccess.ts               # Role access hook
├── pages/
│   ├── LoginPage.tsx                   # Giriş sayfası
│   ├── RegisterPage.tsx                # Kayıt sayfası
│   ├── UnauthorizedPage.tsx            # Yetkisiz erişim sayfası
│   ├── StudentDashboardPage.tsx        # Öğrenci dashboard
│   ├── TeacherDashboardPage.tsx        # Öğretmen dashboard
│   ├── ParentDashboardPage.tsx         # Veli dashboard
│   ├── AdminDashboardPage.tsx          # Admin dashboard
│   ├── ProfilePage.tsx                 # Profil sayfası
│   ├── SettingsPage.tsx                # Ayarlar sayfası
│   ├── TeacherClassesPage.tsx          # Öğretmen sınıfları
│   ├── ParentChildrenPage.tsx          # Veli çocukları
│   └── RBACTestPage.tsx               # RBAC test sayfası
├── services/
│   └── authService.ts                  # Authentication servisi
├── utils/
│   └── apiHelpers.ts                   # API yardımcı fonksiyonları
└── types.ts                            # TypeScript tip tanımları
```

## 🔐 Rol Tanımları

### 1. Öğrenci (ogrenci)
**İzinler:**
- Dashboard okuma
- Sınav oluşturma ve katılma
- Profil okuma ve güncelleme
- Chat kullanımı
- Öğrenme yolu erişimi

**Sayfalar:**
- `/dashboard` - Ana dashboard
- `/exams` - Sınav listesi
- `/exam/start` - Sınav başlatma
- `/learning-path` - Öğrenme yolu
- `/chat` - AI sohbet
- `/profile` - Profil ayarları

### 2. Öğretmen (ogretmen)
**İzinler:**
- Dashboard okuma
- Öğrenci listesi okuma
- Sınıf yönetimi
- Sınav oluşturma ve güncelleme
- Rapor okuma
- İçerik oluşturma

**Sayfalar:**
- `/teacher/dashboard` - Öğretmen dashboard
- `/teacher/classes` - Sınıf yönetimi
- `/teacher/students` - Öğrenci listesi
- `/teacher/exams` - Sınav yönetimi
- `/teacher/reports` - Raporlar

### 3. Veli (veli)
**İzinler:**
- Dashboard okuma
- Çocuk ilerleme takibi
- Rapor okuma
- Bildirim okuma
- Profil okuma ve güncelleme

**Sayfalar:**
- `/parent/dashboard` - Veli dashboard
- `/parent/children` - Çocuk listesi
- `/parent/reports` - İlerleme raporları
- `/parent/notifications` - Bildirimler

### 4. Admin (admin)
**İzinler:**
- Tüm kaynaklara tam erişim (`*:*`)
- Kullanıcı yönetimi
- İçerik yönetimi
- Sistem ayarları
- Analitik veriler

**Sayfalar:**
- `/admin/dashboard` - Admin dashboard
- `/admin/panel` - Admin panel
- `/admin/users` - Kullanıcı yönetimi
- `/admin/content` - İçerik yönetimi
- `/admin/settings` - Sistem ayarları
- `/rbac-test` - RBAC test sayfası

## 🛠️ Kullanım Örnekleri

### 1. Korumalı Route Kullanımı

```tsx
import { ProtectedRoute } from '../components/Auth/ProtectedRoute'

<Route 
  path="/admin/dashboard" 
  element={
    <ProtectedRoute requiredRoles={['admin']}>
      <AdminDashboardPage />
    </ProtectedRoute>
  } 
/>
```

### 2. Rol Bazlı Bileşen Kullanımı

```tsx
import { RoleBasedComponent, AdminOnly } from '../components/Common/RoleBasedComponent'

// Genel kullanım
<RoleBasedComponent allowedRoles={['ogretmen', 'admin']}>
  <TeacherOnlyContent />
</RoleBasedComponent>

// Kısayol kullanımı
<AdminOnly fallback={<div>Admin değilsiniz</div>}>
  <AdminContent />
</AdminOnly>
```

### 3. İzin Kontrolü

```tsx
import { useRoleAccess } from '../hooks/useRoleAccess'

const { canEdit, canDelete, hasAccess } = useRoleAccess({
  allowedRoles: ['ogretmen'],
  requiredPermissions: [{ resource: 'students', action: 'read' }]
})

if (canEdit('content')) {
  // İçerik düzenleme UI'ı göster
}
```

### 4. Authentication Hook Kullanımı

```tsx
import { useAuth } from '../hooks/useAuth'

const { user, isAuthenticated, hasRole, logout } = useAuth()

if (hasRole('admin')) {
  // Admin özelliklerini göster
}
```

## 🔧 API Entegrasyonu

### Authentication Endpoints
- `POST /api/v1/auth/login` - Kullanıcı girişi
- `POST /api/v1/auth/register` - Kullanıcı kaydı
- `POST /api/v1/auth/refresh` - Token yenileme
- `POST /api/v1/auth/logout` - Çıkış yapma
- `GET /api/v1/auth/me` - Kullanıcı bilgileri

### Authorization Headers
```typescript
headers: {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
}
```

## 🧪 Test Etme

RBAC sistemini test etmek için:

1. **Admin hesabıyla giriş yapın**
2. `/rbac-test` sayfasına gidin
3. Rol ve izin kontrollerini inceleyin
4. Farklı rollerle giriş yaparak test edin

## 🚀 Gelecek Geliştirmeler

- [ ] Multi-tenant desteği
- [ ] Dinamik rol oluşturma
- [ ] İzin kalıtımı
- [ ] Audit logging
- [ ] 2FA entegrasyonu

## 📝 Notlar

- Tüm API çağrıları otomatik token yönetimi ile yapılır
- Token süresi dolduğunda otomatik yenileme yapılır
- Yetkisiz erişim durumunda kullanıcı uygun sayfaya yönlendirilir
- Rol değişiklikleri için sayfa yenilenmesi gerekebilir

## 🔒 Güvenlik

- JWT token'lar localStorage'da saklanır
- Refresh token ile güvenli token yenileme
- API çağrılarında otomatik authorization header
- XSS ve CSRF koruması
- Input validation ve sanitization