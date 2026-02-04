# App Store Publishing Guide - Kiro Mobile App

Complete guide for publishing the Kiro mobile application to iOS App Store and Google Play Store.

## Table of Contents

1. [iOS App Store Publishing](#ios-app-store-publishing)
2. [Google Play Store Publishing](#google-play-store-publishing)
3. [App Metadata](#app-metadata)
4. [Screenshots and Media](#screenshots-and-media)
5. [Release Checklist](#release-checklist)

---

## iOS App Store Publishing

### Prerequisites

- **Apple Developer Account** ($99/year)
- **Mac computer** with Xcode installed
- **Provisioning profiles** and certificates
- **App Store Connect** access

### 1. App Store Connect Setup

#### A. Create App ID

1. Go to [Apple Developer Portal](https://developer.apple.com/)
2. Navigate to **Certificates, Identifiers & Profiles**
3. Select **Identifiers** → Click **+** button
4. Choose **App IDs** → Select **App**
5. Fill in details:
   - **Description**: Kiro - University Exam Preparation
   - **Bundle ID**: `com.kiro.app` (explicit)
   - **Capabilities**: Enable required capabilities:
     - Push Notifications
     - Sign in with Apple (if applicable)
     - Associated Domains (for deep linking)

#### B. Create Certificates

**Distribution Certificate:**
```bash
# On your Mac, open Keychain Access
# Navigate to: Keychain Access → Certificate Assistant → Request a Certificate from a Certificate Authority
# Save the CSR file
```

1. In Apple Developer Portal → **Certificates**
2. Click **+** → Select **Apple Distribution**
3. Upload the CSR file
4. Download and install the certificate

#### C. Create Provisioning Profile

1. In Apple Developer Portal → **Profiles**
2. Click **+** → Select **App Store**
3. Select the App ID you created
4. Select the Distribution Certificate
5. Download the provisioning profile
6. Double-click to install in Xcode

#### D. Create App in App Store Connect

1. Go to [App Store Connect](https://appstoreconnect.apple.com/)
2. Click **My Apps** → **+** → **New App**
3. Fill in the details:
   - **Platforms**: iOS
   - **Name**: Kiro
   - **Primary Language**: Turkish
   - **Bundle ID**: Select `com.kiro.app`
   - **SKU**: `kiro-ios-001`
   - **User Access**: Full Access

### 2. Configure Xcode Project

#### Update Build Settings

**In `ios/Kiro.xcworkspace`:**

1. Select the project → **Signing & Capabilities**
2. **Team**: Select your Apple Developer Team
3. **Bundle Identifier**: `com.kiro.app`
4. **Signing**: Automatically manage signing
5. **Provisioning Profile**: Select the distribution profile

#### Update Info.plist

```xml
<!-- ios/Kiro/Info.plist -->
<key>CFBundleDisplayName</key>
<string>Kiro</string>
<key>CFBundleShortVersionString</key>
<string>1.0.0</string>
<key>CFBundleVersion</key>
<string>1</string>

<!-- Privacy Descriptions -->
<key>NSCameraUsageDescription</key>
<string>Kiro optik form taraması için kamera erişimi gerektirir</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>Kiro fotoğraf kaydetmek için galeri erişimi gerektirir</string>
<key>NSMicrophoneUsageDescription</key>
<string>Kiro sesli komutlar için mikrofon erişimi gerektirir</string>
<key>NSSpeechRecognitionUsageDescription</key>
<string>Kiro sesli komutlar için ses tanıma kullanır</string>
```

#### App Transport Security

```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <false/>
    <key>NSExceptionDomains</key>
    <dict>
        <key>api.kiro.app</key>
        <dict>
            <key>NSExceptionAllowsInsecureHTTPLoads</key>
            <false/>
            <key>NSIncludesSubdomains</key>
            <true/>
        </dict>
    </dict>
</dict>
```

### 3. Build and Archive

#### Configure Release Build

**In `ios/Kiro/AppDelegate.mm`:**
```objc
// Disable dev mode in production
#if DEBUG
  [FBSDKSettings setIsDebugEnabled:YES];
#else
  [FBSDKSettings setIsDebugEnabled:NO];
#endif
```

#### Build Archive

1. In Xcode, select **Product** → **Archive**
2. Wait for the build to complete
3. Once done, the **Organizer** window opens

#### Upload to App Store Connect

1. In **Organizer**, select the archive
2. Click **Distribute App**
3. Select **App Store Connect**
4. Select **Upload**
5. Choose signing options (automatic recommended)
6. Click **Upload**

**Alternative: Command Line**

```bash
cd ios

# Clean build
xcodebuild clean -workspace Kiro.xcworkspace -scheme Kiro

# Archive
xcodebuild archive \
  -workspace Kiro.xcworkspace \
  -scheme Kiro \
  -archivePath ./build/Kiro.xcarchive

# Export IPA
xcodebuild -exportArchive \
  -archivePath ./build/Kiro.xcarchive \
  -exportPath ./build \
  -exportOptionsPlist ExportOptions.plist

# Upload with Transporter or altool
xcrun altool --upload-app \
  --type ios \
  --file ./build/Kiro.ipa \
  --username "your-apple-id@email.com" \
  --password "app-specific-password"
```

**ExportOptions.plist:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>app-store</string>
    <key>teamID</key>
    <string>YOUR_TEAM_ID</string>
    <key>uploadBitcode</key>
    <false/>
    <key>uploadSymbols</key>
    <true/>
</dict>
</plist>
```

### 4. Complete App Store Connect Information

1. Go to **App Store Connect** → **My Apps** → **Kiro**
2. Select **1.0 Prepare for Submission**

#### App Information

- **Name**: Kiro
- **Subtitle**: Üniversite Sınavlarına Hazırlık
- **Category**:
  - Primary: Education
  - Secondary: Productivity
- **Content Rights**: Contains third-party content
- **Age Rating**: 4+ (No objectionable content)

#### Pricing and Availability

- **Price**: Free
- **Availability**: All countries
- **Educational Discount**: Yes (if applicable)

#### App Privacy

Configure privacy details:
- **Data Collection**: Analytics, user accounts
- **Data Usage**: Personalization, app functionality
- **Tracking**: No (or configure if using third-party analytics)

#### Version Information

- **Version**: 1.0.0
- **Copyright**: 2025 Kiro Team
- **What's New**: Initial release with study tools, practice exams, and gamification

### 5. Submit for Review

1. Add all required screenshots (see Screenshots section)
2. Fill in review information:
   - **Demo Account**: Provide test credentials
   - **Notes**: Any special instructions for reviewers
   - **Contact Information**: Support email and phone
3. Click **Submit for Review**

### 6. Review Process

**Timeline**: 24-48 hours (typically)

**Common Rejection Reasons:**
- Missing privacy policy
- Incomplete metadata
- App crashes on launch
- Missing required features in screenshots
- Privacy permission descriptions unclear

**After Approval:**
- App status changes to "Ready for Sale"
- Available on App Store within 24 hours

---

## Google Play Store Publishing

### Prerequisites

- **Google Play Developer Account** ($25 one-time fee)
- **Signed APK/AAB**
- **Google Play Console** access

### 1. Google Play Console Setup

#### A. Create Application

1. Go to [Google Play Console](https://play.google.com/console/)
2. Click **Create app**
3. Fill in details:
   - **App name**: Kiro
   - **Default language**: Turkish
   - **App or game**: App
   - **Free or paid**: Free
   - Accept declarations

#### B. Set Up App

Complete all required sections:

**App Access:**
- All features available without restrictions
- Or provide test account if login required

**Ads:**
- No (or Yes if using ads)

**Content Rating:**
- Complete questionnaire
- Expected rating: PEGI 3 / ESRB Everyone

**Target Audience:**
- Age groups: 13+ (high school and university students)

**News Apps:**
- No

**COVID-19 Contact Tracing:**
- No

**Data Safety:**
- Complete data collection and sharing form
- Specify what data is collected
- Data security practices

**Privacy Policy:**
- URL: https://kiro.app/privacy-policy

### 2. Configure Android Project

#### Update build.gradle

**`android/app/build.gradle`:**
```gradle
android {
    defaultConfig {
        applicationId "com.kiro.app"
        minSdkVersion 23
        targetSdkVersion 33
        versionCode 1
        versionName "1.0.0"
    }

    signingConfigs {
        release {
            storeFile file('kiro-release-key.keystore')
            storePassword System.getenv("KEYSTORE_PASSWORD")
            keyAlias System.getenv("KEY_ALIAS")
            keyPassword System.getenv("KEY_PASSWORD")
        }
    }

    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

#### Create Keystore

```bash
cd android/app

# Generate keystore
keytool -genkeypair -v \
  -storetype PKCS12 \
  -keystore kiro-release-key.keystore \
  -alias kiro-release \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000

# You'll be prompted for:
# - Keystore password
# - Key password
# - Your name and organization details

# IMPORTANT: Keep the keystore file and passwords secure!
# Store in password manager and backup safely
```

**Add to `.gitignore`:**
```
*.keystore
```

**Set environment variables:**
```bash
# Add to ~/.bashrc or ~/.zshrc
export KEYSTORE_PASSWORD="your-keystore-password"
export KEY_ALIAS="kiro-release"
export KEY_PASSWORD="your-key-password"
```

### 3. Build Release APK/AAB

#### Build App Bundle (Recommended)

```bash
cd android

# Clean
./gradlew clean

# Build release AAB
./gradlew bundleRelease

# Output: android/app/build/outputs/bundle/release/app-release.aab
```

#### Build Release APK

```bash
# Build release APK
./gradlew assembleRelease

# Output: android/app/build/outputs/apk/release/app-release.apk
```

#### Test Release Build

```bash
# Install on device
adb install android/app/build/outputs/apk/release/app-release.apk

# Test thoroughly:
# - App launches correctly
# - All features work
# - No crashes
# - API connections work
```

### 4. Upload to Google Play Console

#### A. Internal Testing (Recommended First)

1. In Play Console → **Testing** → **Internal testing**
2. Create new release
3. Upload AAB file
4. Fill in release notes
5. Add internal testers (emails)
6. Save and publish

#### B. Production Release

1. In Play Console → **Production**
2. Create new release
3. Upload AAB file
4. **Release details**:
   - **Release name**: 1.0.0
   - **Release notes** (Turkish):
     ```
     🎉 Kiro ilk sürümü yayında!

     ✨ Özellikler:
     • TYT, AYT, DGS, KPSS soru bankaları
     • Kişiselleştirilmiş çalışma planları
     • Yapay zeka destekli soru çözümleri
     • Detaylı performans analizi
     • Gamification sistemi (rozetler, sıralama)
     • Offline çalışma modu
     • Optik form tarayıcı
     • Sesli komutlar
     • Karanlık mod

     📚 Üniversite sınavlarına hazırlığınızı Kiro ile başlatın!
     ```
5. **Rollout percentage**: 100% (or staged rollout: 10%, 25%, 50%, 100%)
6. Click **Review release**
7. Click **Start rollout to Production**

### 5. Google Play Review Process

**Timeline**: A few hours to a few days

**Review Status:**
- **In review**: Being reviewed
- **Pending publication**: Approved, waiting to go live
- **Published**: Live on Google Play Store

**Common Rejection Reasons:**
- Misleading screenshots or description
- Privacy policy issues
- Permissions not justified
- App crashes
- Missing required features

---

## App Metadata

### App Store (iOS)

#### App Name
```
Kiro
```

#### Subtitle (30 characters)
```
Üniversite Sınav Hazırlık
```

#### Description (4000 characters max)

```
Kiro ile üniversite sınavlarına (TYT, AYT, DGS, KPSS) hazırlığınızı üst seviyeye taşıyın!

🎯 KAPSAMLI SORU BANKASI
• 100.000+ güncel sınav sorusu
• TYT, AYT, DGS, KPSS tüm dersler
• Müfredata uygun içerik
• Düzenli olarak güncellenen sorular

📊 KİŞİSELLEŞTİRİLMİŞ ÖĞRENİM
• Yapay zeka destekli öğrenme planı
• Zayıf konularınıza özel sorular
• Detaylı performans analizi
• İlerleme takibi ve raporlama

🤖 YAPAY ZEKA DESTEĞİ
• Soru çözümlerinde adım adım açıklama
• Akıllı soru önerileri
• Kişisel çalışma koçu
• Anlamadığınız konularda yapay zeka desteği

🎮 GAMİFİKASYON
• Seviye atlama sistemi
• Başarı rozetleri
• Liderlik sıralaması
• Günlük hedefler ve ödüller

⚡ GELIŞMIŞ ÖZELLİKLER
• Offline çalışma modu - internetsiz soru çözün
• Optik form tarayıcı - deneme sınavlarınızı tarayın
• Sesli komutlar - eller serbest kullanım
• Karanlık mod - göz dostu arayüz
• Veri tasarrufu modu - kotanızı koruyun

📚 ÇALIŞMA ARAÇLARI
• Deneme sınavları
• Konu anlatımları
• Video çözümler
• Formül kartları
• Özet notlar

👥 SOSYAL ÖĞRENİM
• Öğretmenlerle iletişim
• Öğrenci forumları
• Soru-cevap platformu
• Grup çalışmaları

📈 ANALİZ VE RAPORLAMA
• Detaylı performans grafikleri
• Konu bazlı başarı analizi
• Hedef belirleme ve takip
• Gelişim raporları
• Tahmin edilen başarı oranı

🎯 HEDEFİNİZE ULAŞIN
Kiro, binlerce öğrencinin üniversite hayallerine ulaşmasına yardımcı oldu. Siz de katılın!

📱 ÜCRETSİZ İNDİRİN
Hemen indirin ve çalışmaya başlayın. Premium özellikler için uygulama içi satın alma seçenekleri mevcuttur.

📧 DESTEK
Sorularınız için: destek@kiro.app
Web: https://kiro.app

Başarılar dileriz! 🎓
```

#### Keywords (100 characters max)
```
tyt,ayt,yks,dgs,kpss,sınav,üniversite,soru,test,deneme,eğitim,hazırlık
```

#### Promotional Text (170 characters) - Optional
```
🎉 İlk sürüm! 100.000+ soru, yapay zeka desteği, offline mod, optik form tarayıcı ve daha fazlası. Ücretsiz indirin!
```

#### Support URL
```
https://kiro.app/support
```

#### Marketing URL
```
https://kiro.app
```

#### Privacy Policy URL
```
https://kiro.app/privacy-policy
```

### Google Play Store

#### Short Description (80 characters max)
```
TYT, AYT, DGS, KPSS hazırlık. 100K+ soru, yapay zeka, offline mod!
```

#### Full Description (4000 characters max)

```
🎓 Kiro - Üniversite Sınavlarına Akıllı Hazırlık

Kiro ile TYT, AYT, DGS, KPSS sınavlarına en etkili şekilde hazırlanın! Yapay zeka destekli öğrenme platformu ile hedefinize ulaşın.

📚 SORU BANKASI
✅ 100.000+ güncel soru
✅ TYT, AYT, DGS, KPSS tüm dersler
✅ Müfredata uygun içerik
✅ Düzenli güncellemeler

🤖 YAPAY ZEKA DESTEĞİ
✅ Kişiselleştirilmiş öğrenme planı
✅ Zayıf konularınıza odaklanma
✅ Adım adım çözüm açıklamaları
✅ Akıllı soru önerileri

📊 PERFORMANS ANALİZİ
✅ Detaylı grafik ve raporlar
✅ Konu bazlı başarı takibi
✅ İlerleme izleme
✅ Hedef belirleme

🎮 MOTİVASYON SİSTEMİ
✅ Seviye atlama
✅ Başarı rozetleri
✅ Liderlik sıralaması
✅ Günlük hedefler

⚡ GELİŞMİŞ ÖZELLİKLER
✅ 📴 Offline Mod - İnternetsiz çalışın
✅ 📷 Optik Form Tarayıcı - Deneme kağıtlarınızı tarayın
✅ 🎤 Sesli Komutlar - Eller serbest kullanım
✅ 🌙 Karanlık Mod - Göz dostu arayüz
✅ 📶 Veri Tasarrufu - Kotanızı koruyun

📖 ÇALIŞMA ARAÇLARI
• Deneme sınavları
• Video konu anlatımları
• Formül kartları
• Özet notlar
• EBA entegrasyonu

👥 SOSYAL ÖĞRENİM
• Öğretmen desteği
• Öğrenci forumları
• Soru-cevap platformu
• Canlı dersler

🎯 BAŞARI HİKAYELERİ
Binlerce öğrenci Kiro ile hedeflerine ulaştı. Sıradaki siz olun!

💎 ÜCRETSİZ BAŞLAYIN
Temel özellikler tamamen ücretsiz! Premium paketler ile tüm özelliklere erişin.

📞 İLETİŞİM
E-posta: destek@kiro.app
Web: https://kiro.app
Instagram: @kiro.app

Başarılar! 🎓✨
```

---

## Screenshots and Media

### iOS App Store Requirements

**Required Screenshots:**

1. **iPhone 6.7" (iPhone 14 Pro Max)** - Required
   - Resolution: 1290 x 2796 pixels
   - At least 3 screenshots, maximum 10

2. **iPhone 6.5" (iPhone 11 Pro Max, XS Max)** - Required
   - Resolution: 1242 x 2688 pixels
   - At least 3 screenshots, maximum 10

3. **iPad Pro 12.9" (3rd gen)** - Required
   - Resolution: 2048 x 2732 pixels
   - At least 3 screenshots, maximum 10

**Optional:**
- App Preview videos (15-30 seconds)

### Android Play Store Requirements

**Required Screenshots:**

1. **Phone Screenshots**
   - Minimum 2, maximum 8
   - JPEG or PNG (no alpha)
   - Minimum dimension: 320px
   - Maximum dimension: 3840px
   - Recommended: 1080 x 1920 pixels (9:16 ratio)

2. **7-inch Tablet** (Optional)
   - 1200 x 1920 pixels

3. **10-inch Tablet** (Optional)
   - 1600 x 2560 pixels

**Feature Graphic** (Required)
- 1024 x 500 pixels
- JPEG or 24-bit PNG (no alpha)

**App Icon**
- 512 x 512 pixels
- 32-bit PNG (with alpha)

### Screenshot Content Recommendations

**Screenshot 1: Home Dashboard**
- Show main dashboard
- Highlight key features
- Display statistics

**Screenshot 2: Question Solving**
- Show a sample question
- Highlight AI explanation feature
- Show progress tracking

**Screenshot 3: Performance Analytics**
- Display graphs and charts
- Show subject breakdown
- Highlight personalization

**Screenshot 4: Gamification**
- Show badges and achievements
- Display leaderboard
- Highlight streak tracking

**Screenshot 5: Study Plan**
- Show AI-generated study plan
- Display calendar view
- Highlight recommendations

**Screenshot 6: OMR Scanner**
- Show camera scanning interface
- Display results
- Highlight accuracy

**Screenshot 7: Offline Mode**
- Show downloaded content
- Highlight offline capability
- Display sync status

**Screenshot 8: Dark Mode**
- Show beautiful dark theme
- Highlight eye comfort
- Display theme switching

### Screenshot Generation Tools

#### Using Fastlane Snapshot (iOS)

**Install:**
```bash
gem install fastlane
fastlane snapshot init
```

**Configure `Snapfile`:**
```ruby
devices([
  "iPhone 14 Pro Max",
  "iPhone 11 Pro Max",
  "iPad Pro (12.9-inch) (6th generation)"
])

languages([
  "tr-TR",
  "en-US"
])

scheme("Kiro")

output_directory("./screenshots")
```

**Run:**
```bash
fastlane snapshot
```

#### Using Fastlane Screengrab (Android)

**Configure:**
```bash
fastlane screengrab init
```

**Run:**
```bash
fastlane screengrab
```

#### Manual Screenshots

1. Use device simulators/emulators
2. Set up demo data
3. Capture screenshots using:
   - iOS: `Cmd + S` in Simulator
   - Android: `Ctrl + S` in Emulator
4. Edit with design tool (Figma, Sketch, Photoshop)
5. Add text overlays and highlights
6. Export in required resolutions

### Screenshot Template

Use tools like:
- **Figma** (free, web-based)
- **Sketch** (Mac only)
- **Adobe Photoshop**
- **Canva** (easy templates)

**Template Structure:**
```
+----------------------------------+
|                                  |
|    [Screenshot of app]           |
|                                  |
|                                  |
+----------------------------------+
|                                  |
|  "Feature Title"                 |
|  Short description of feature    |
|                                  |
+----------------------------------+
```

---

## Release Checklist

### Pre-Release

**Code:**
- [ ] All features complete and tested
- [ ] No critical bugs
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Performance optimized
- [ ] Memory leaks fixed
- [ ] Crash-free for 99.9%

**Build:**
- [ ] Version number updated
- [ ] Build number incremented
- [ ] Release build tested on real devices
- [ ] All API endpoints point to production
- [ ] Analytics configured
- [ ] Crash reporting enabled (Firebase Crashlytics)
- [ ] Environment variables set correctly

**App Store Assets:**
- [ ] App icon (all sizes)
- [ ] Screenshots (all required sizes)
- [ ] App description written
- [ ] Keywords researched
- [ ] Privacy policy published
- [ ] Support URL active
- [ ] Demo account created for reviewers

**Legal:**
- [ ] Privacy policy complete
- [ ] Terms of service complete
- [ ] Content rating completed
- [ ] Age rating appropriate
- [ ] Copyright information correct

**iOS Specific:**
- [ ] Provisioning profiles configured
- [ ] Certificates valid
- [ ] App Store Connect app created
- [ ] TestFlight beta tested
- [ ] Push notifications tested
- [ ] IAP (if any) configured

**Android Specific:**
- [ ] Keystore created and backed up
- [ ] ProGuard rules configured
- [ ] App signing configured
- [ ] Google Play Console setup
- [ ] Internal testing completed
- [ ] APK/AAB size optimized

### Post-Release

**Monitoring:**
- [ ] Monitor crash reports daily
- [ ] Check app store reviews
- [ ] Monitor analytics
- [ ] Track user acquisition
- [ ] Monitor server performance
- [ ] Check API error rates

**User Feedback:**
- [ ] Respond to reviews (within 24-48 hours)
- [ ] Address critical bugs immediately
- [ ] Collect feature requests
- [ ] Plan updates based on feedback

**Updates:**
- [ ] Bug fix releases (as needed)
- [ ] Feature updates (monthly/quarterly)
- [ ] Keep dependencies updated
- [ ] Monitor OS version adoption
- [ ] Plan for new OS features

---

## Release Automation

### Fastlane Configuration

**Install Fastlane:**
```bash
gem install fastlane
```

**Initialize:**
```bash
cd ios
fastlane init

cd ../android
fastlane init
```

**iOS Fastfile** (`ios/fastlane/Fastfile`):
```ruby
default_platform(:ios)

platform :ios do
  desc "Push a new beta build to TestFlight"
  lane :beta do
    increment_build_number(xcodeproj: "Kiro.xcodeproj")
    build_app(workspace: "Kiro.xcworkspace", scheme: "Kiro")
    upload_to_testflight
  end

  desc "Push a new release build to the App Store"
  lane :release do
    increment_build_number(xcodeproj: "Kiro.xcodeproj")
    build_app(workspace: "Kiro.xcworkspace", scheme: "Kiro")
    upload_to_app_store
  end
end
```

**Android Fastfile** (`android/fastlane/Fastfile`):
```ruby
default_platform(:android)

platform :android do
  desc "Deploy a new version to the Google Play"
  lane :deploy do
    gradle(task: "clean bundleRelease")
    upload_to_play_store
  end

  desc "Deploy to internal testing"
  lane :internal do
    gradle(task: "clean bundleRelease")
    upload_to_play_store(track: 'internal')
  end
end
```

**Run:**
```bash
# iOS TestFlight
cd ios && fastlane beta

# iOS App Store
cd ios && fastlane release

# Android Internal
cd android && fastlane internal

# Android Production
cd android && fastlane deploy
```

---

## Summary

This guide covers the complete process of publishing the Kiro mobile app to both iOS App Store and Google Play Store:

✅ **iOS App Store** (114.1)
- Apple Developer account setup
- App Store Connect configuration
- Certificates and provisioning profiles
- Xcode project configuration
- Build and archive process
- Submission and review

✅ **Google Play Store** (114.2)
- Google Play Console setup
- Keystore generation
- Release build configuration
- AAB/APK building
- Upload and publishing
- Review process

✅ **App Metadata** (114.3)
- App descriptions (iOS & Android)
- Keywords and categories
- Pricing and availability
- Privacy policy
- Support URLs

✅ **Screenshots** (114.4)
- Required sizes for each platform
- Content recommendations
- Screenshot generation tools
- Design templates
- Feature graphics

The guide also includes release checklists, automation with Fastlane, and post-release monitoring strategies.
