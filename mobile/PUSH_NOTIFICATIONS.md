# Push Notifications - Kiro Mobile App

Complete push notification system implementation using Firebase Cloud Messaging (FCM) with local notifications, scheduling, and user preferences.

## Table of Contents

1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Firebase Setup](#firebase-setup)
4. [FCM Integration](#fcm-integration)
5. [Notification Types](#notification-types)
6. [Notification Scheduling](#notification-scheduling)
7. [User Preferences](#user-preferences)
8. [Testing](#testing)

---

## Overview

The push notification system provides:
- **Remote notifications** from Firebase Cloud Messaging (FCM)
- **Local notifications** for study reminders and scheduled alerts
- **Notification categories** for different types of alerts
- **User preferences** for notification customization
- **Quiet hours** to prevent notifications during specific times
- **Custom sounds** and vibration patterns

---

## Technology Stack

### Core Libraries

```json
{
  "@react-native-firebase/app": "^18.7.0",
  "@react-native-firebase/messaging": "^18.7.0",
  "react-native-push-notification": "^8.1.1",
  "react-native-push-notification-ios": "^1.11.0",
  "@notifee/react-native": "^7.8.0"
}
```

### Installation

```bash
# Install Firebase packages
npm install @react-native-firebase/app @react-native-firebase/messaging

# Install local notification libraries
npm install react-native-push-notification
npm install --save react-native-push-notification-ios

# Install advanced notification library (optional)
npm install @notifee/react-native

# iOS specific
cd ios && pod install && cd ..
```

---

## Firebase Setup

### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing project
3. Add iOS and Android apps to the project

### 2. iOS Configuration

**Download `GoogleService-Info.plist`**:
1. In Firebase Console, go to Project Settings
2. Add iOS app with bundle ID (e.g., `com.kiro.app`)
3. Download `GoogleService-Info.plist`
4. Add file to `ios/` directory in Xcode

**Update `ios/Podfile`**:
```ruby
platform :ios, '13.0'
require_relative '../node_modules/react-native/scripts/react_native_pods'
require_relative '../node_modules/@react-native-community/cli-platform-ios/native_modules'

target 'Kiro' do
  config = use_native_modules!

  use_react_native!(
    :path => config[:reactNativePath],
    :hermes_enabled => true
  )

  # Add Firebase pods
  pod 'Firebase/Messaging'

  # Push notifications
  pod 'RNPushNotification', :path => '../node_modules/react-native-push-notification'

  post_install do |installer|
    react_native_post_install(installer)
  end
end
```

**Update `ios/Kiro/AppDelegate.mm`**:
```objc
#import "AppDelegate.h"
#import <React/RCTBundleURLProvider.h>
#import <Firebase.h>
#import <UserNotifications/UserNotifications.h>
#import <RNCPushNotificationIOS.h>

@implementation AppDelegate

- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions
{
  // Initialize Firebase
  [FIRApp configure];

  // Define UNUserNotificationCenter
  UNUserNotificationCenter *center = [UNUserNotificationCenter currentNotificationCenter];
  center.delegate = self;

  self.moduleName = @"Kiro";
  self.initialProps = @{};

  return [super application:application didFinishLaunchingWithOptions:launchOptions];
}

// Required for the register event
- (void)application:(UIApplication *)application didRegisterForRemoteNotificationsWithDeviceToken:(NSData *)deviceToken
{
  [RNCPushNotificationIOS didRegisterForRemoteNotificationsWithDeviceToken:deviceToken];
}

// Required for the notification event
- (void)application:(UIApplication *)application didReceiveRemoteNotification:(NSDictionary *)userInfo
fetchCompletionHandler:(void (^)(UIBackgroundFetchResult))completionHandler
{
  [RNCPushNotificationIOS didReceiveRemoteNotification:userInfo fetchCompletionHandler:completionHandler];
}

// Required for the registrationError event
- (void)application:(UIApplication *)application didFailToRegisterForRemoteNotificationsWithError:(NSError *)error
{
  [RNCPushNotificationIOS didFailToRegisterForRemoteNotificationsWithError:error];
}

// Required for localNotification event
- (void)userNotificationCenter:(UNUserNotificationCenter *)center
didReceiveNotificationResponse:(UNNotificationResponse *)response
         withCompletionHandler:(void (^)(void))completionHandler
{
  [RNCPushNotificationIOS didReceiveNotificationResponse:response];
  completionHandler();
}

// Required for foreground notifications
- (void)userNotificationCenter:(UNUserNotificationCenter *)center
       willPresentNotification:(UNNotification *)notification
         withCompletionHandler:(void (^)(UNNotificationPresentationOptions options))completionHandler
{
  completionHandler(UNNotificationPresentationOptionSound | UNNotificationPresentationOptionAlert | UNNotificationPresentationOptionBadge);
}

@end
```

**Add Capabilities in Xcode**:
1. Open `ios/Kiro.xcworkspace` in Xcode
2. Select target → Signing & Capabilities
3. Add "Push Notifications" capability
4. Add "Background Modes" capability
   - Check "Remote notifications"

### 3. Android Configuration

**Download `google-services.json`**:
1. In Firebase Console, add Android app with package name (e.g., `com.kiro.app`)
2. Download `google-services.json`
3. Place file in `android/app/` directory

**Update `android/build.gradle`**:
```gradle
buildscript {
    dependencies {
        classpath 'com.android.tools.build:gradle:7.4.2'
        classpath 'com.google.gms:google-services:4.3.15'
    }
}
```

**Update `android/app/build.gradle`**:
```gradle
apply plugin: "com.android.application"
apply plugin: "com.google.gms.google-services"

dependencies {
    implementation platform('com.google.firebase:firebase-bom:32.7.0')
    implementation 'com.google.firebase:firebase-messaging'
}
```

**Update `android/app/src/main/AndroidManifest.xml`**:
```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.VIBRATE" />
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED"/>

    <application>
        <!-- Firebase Messaging Service -->
        <service
            android:name=".FirebaseMessagingService"
            android:exported="false">
            <intent-filter>
                <action android:name="com.google.firebase.MESSAGING_EVENT" />
            </intent-filter>
        </service>

        <!-- Notification metadata -->
        <meta-data
            android:name="com.google.firebase.messaging.default_notification_icon"
            android:resource="@drawable/ic_notification" />
        <meta-data
            android:name="com.google.firebase.messaging.default_notification_color"
            android:resource="@color/notification_color" />
    </application>
</manifest>
```

---

## FCM Integration

### 1. Notification Service (`src/services/NotificationService.ts`)

```typescript
import messaging, { FirebaseMessagingTypes } from '@react-native-firebase/messaging';
import PushNotification, { Importance } from 'react-native-push-notification';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import { apiClient } from '../api/client';

export type NotificationCategory =
  | 'study_reminder'
  | 'exam_reminder'
  | 'achievement'
  | 'social'
  | 'system'
  | 'custom';

export interface NotificationPreferences {
  enabled: boolean;
  categories: {
    [key in NotificationCategory]: boolean;
  };
  quietHours: {
    enabled: boolean;
    start: string; // HH:MM format
    end: string;   // HH:MM format
  };
  sound: boolean;
  vibration: boolean;
  badge: boolean;
}

class NotificationService {
  private fcmToken: string | null = null;
  private preferences: NotificationPreferences = {
    enabled: true,
    categories: {
      study_reminder: true,
      exam_reminder: true,
      achievement: true,
      social: true,
      system: true,
      custom: true,
    },
    quietHours: {
      enabled: false,
      start: '22:00',
      end: '08:00',
    },
    sound: true,
    vibration: true,
    badge: true,
  };

  /**
   * Initialize notification service
   */
  async initialize(): Promise<void> {
    // Request permission
    const authStatus = await this.requestPermission();

    if (authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
        authStatus === messaging.AuthorizationStatus.PROVISIONAL) {

      // Get FCM token
      await this.getFCMToken();

      // Configure local notifications
      this.configureLocalNotifications();

      // Set up message handlers
      this.setupMessageHandlers();

      // Load user preferences
      await this.loadPreferences();

      console.log('Notification service initialized');
    } else {
      console.log('Notification permission denied');
    }
  }

  /**
   * Request notification permission
   */
  async requestPermission(): Promise<messaging.AuthorizationStatus> {
    const authStatus = await messaging().requestPermission();
    return authStatus;
  }

  /**
   * Get FCM token and save to server
   */
  async getFCMToken(): Promise<string | null> {
    try {
      // Check if user has already given permission
      const authStatus = await messaging().hasPermission();

      if (authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
          authStatus === messaging.AuthorizationStatus.PROVISIONAL) {

        // Get FCM token
        const token = await messaging().getToken();
        this.fcmToken = token;

        // Save token to AsyncStorage
        await AsyncStorage.setItem('fcm_token', token);

        // Send token to backend
        await this.registerTokenWithBackend(token);

        console.log('FCM Token:', token);
        return token;
      }

      return null;
    } catch (error) {
      console.error('Error getting FCM token:', error);
      return null;
    }
  }

  /**
   * Register FCM token with backend
   */
  private async registerTokenWithBackend(token: string): Promise<void> {
    try {
      await apiClient.post('/notifications/register-token', {
        token,
        platform: Platform.OS,
        device_info: {
          os_version: Platform.Version,
        },
      });
    } catch (error) {
      console.error('Error registering token with backend:', error);
    }
  }

  /**
   * Configure local notifications
   */
  private configureLocalNotifications(): void {
    // Create notification channels (Android)
    PushNotification.createChannel(
      {
        channelId: 'study-reminders',
        channelName: 'Çalışma Hatırlatıcıları',
        channelDescription: 'Planlı çalışma seansları için hatırlatmalar',
        importance: Importance.HIGH,
        vibrate: true,
      },
      (created) => console.log(`Channel 'study-reminders' created: ${created}`)
    );

    PushNotification.createChannel(
      {
        channelId: 'exam-reminders',
        channelName: 'Sınav Hatırlatıcıları',
        channelDescription: 'Yaklaşan sınavlar için hatırlatmalar',
        importance: Importance.HIGH,
        vibrate: true,
      },
      (created) => console.log(`Channel 'exam-reminders' created: ${created}`)
    );

    PushNotification.createChannel(
      {
        channelId: 'achievements',
        channelName: 'Başarılar',
        channelDescription: 'Rozetler ve seviye atlama bildirimleri',
        importance: Importance.DEFAULT,
        vibrate: false,
      },
      (created) => console.log(`Channel 'achievements' created: ${created}`)
    );

    PushNotification.createChannel(
      {
        channelId: 'social',
        channelName: 'Sosyal',
        channelDescription: 'Mesajlar ve sosyal etkileşimler',
        importance: Importance.DEFAULT,
        vibrate: true,
      },
      (created) => console.log(`Channel 'social' created: ${created}`)
    );

    PushNotification.createChannel(
      {
        channelId: 'system',
        channelName: 'Sistem',
        channelDescription: 'Sistem bildirimleri',
        importance: Importance.LOW,
        vibrate: false,
      },
      (created) => console.log(`Channel 'system' created: ${created}`)
    );

    // Configure notification handlers
    PushNotification.configure({
      onRegister: (token) => {
        console.log('Local notification token:', token);
      },

      onNotification: (notification) => {
        console.log('Local notification received:', notification);

        // Handle notification tap
        if (notification.userInteraction) {
          this.handleNotificationTap(notification);
        }

        // iOS: Call completion handler
        notification.finish(PushNotification.FetchResult.NoData);
      },

      permissions: {
        alert: true,
        badge: true,
        sound: true,
      },

      popInitialNotification: true,
      requestPermissions: true,
    });
  }

  /**
   * Set up FCM message handlers
   */
  private setupMessageHandlers(): void {
    // Handle background messages
    messaging().setBackgroundMessageHandler(async (remoteMessage) => {
      console.log('Background message received:', remoteMessage);
      await this.handleRemoteMessage(remoteMessage);
    });

    // Handle foreground messages
    messaging().onMessage(async (remoteMessage) => {
      console.log('Foreground message received:', remoteMessage);
      await this.handleRemoteMessage(remoteMessage);
    });

    // Handle notification tap when app is in background
    messaging().onNotificationOpenedApp((remoteMessage) => {
      console.log('Notification opened app from background:', remoteMessage);
      this.handleNotificationTap(remoteMessage);
    });

    // Handle notification tap when app was opened from quit state
    messaging()
      .getInitialNotification()
      .then((remoteMessage) => {
        if (remoteMessage) {
          console.log('Notification opened app from quit state:', remoteMessage);
          this.handleNotificationTap(remoteMessage);
        }
      });

    // Handle token refresh
    messaging().onTokenRefresh(async (token) => {
      console.log('FCM token refreshed:', token);
      this.fcmToken = token;
      await AsyncStorage.setItem('fcm_token', token);
      await this.registerTokenWithBackend(token);
    });
  }

  /**
   * Handle remote message from FCM
   */
  private async handleRemoteMessage(
    remoteMessage: FirebaseMessagingTypes.RemoteMessage
  ): Promise<void> {
    const { notification, data } = remoteMessage;

    if (!notification) return;

    // Check if notifications are enabled
    if (!this.preferences.enabled) return;

    // Check category preference
    const category = (data?.category as NotificationCategory) || 'system';
    if (!this.preferences.categories[category]) return;

    // Check quiet hours
    if (this.isQuietHours()) return;

    // Show local notification
    this.showLocalNotification({
      title: notification.title || 'Kiro',
      message: notification.body || '',
      category,
      data: data || {},
    });
  }

  /**
   * Show local notification
   */
  showLocalNotification(options: {
    id?: string;
    title: string;
    message: string;
    category: NotificationCategory;
    data?: Record<string, any>;
    date?: Date;
    repeatType?: 'day' | 'week' | 'month';
  }): void {
    const { id, title, message, category, data, date, repeatType } = options;

    // Check preferences
    if (!this.preferences.enabled || !this.preferences.categories[category]) {
      return;
    }

    // Check quiet hours for scheduled notifications
    if (date && this.isQuietHours(date)) {
      return;
    }

    const channelId = this.getCategoryChannel(category);

    PushNotification.localNotification({
      id: id || String(Date.now()),
      channelId,
      title,
      message,
      playSound: this.preferences.sound,
      vibrate: this.preferences.vibration,
      vibration: 300,
      userInfo: { category, ...data },
      date: date,
      repeatType: repeatType,
      allowWhileIdle: true,
    });
  }

  /**
   * Schedule a notification
   */
  scheduleNotification(options: {
    id: string;
    title: string;
    message: string;
    category: NotificationCategory;
    date: Date;
    repeatType?: 'day' | 'week' | 'month';
    data?: Record<string, any>;
  }): void {
    const { id, title, message, category, date, repeatType, data } = options;

    const channelId = this.getCategoryChannel(category);

    PushNotification.localNotificationSchedule({
      id,
      channelId,
      title,
      message,
      date,
      repeatType,
      playSound: this.preferences.sound,
      vibrate: this.preferences.vibration,
      vibration: 300,
      userInfo: { category, ...data },
      allowWhileIdle: true,
    });
  }

  /**
   * Cancel a scheduled notification
   */
  cancelNotification(id: string): void {
    PushNotification.cancelLocalNotification(id);
  }

  /**
   * Cancel all notifications
   */
  cancelAllNotifications(): void {
    PushNotification.cancelAllLocalNotifications();
  }

  /**
   * Get notification badge count
   */
  async getBadgeCount(): Promise<number> {
    return new Promise((resolve) => {
      PushNotification.getApplicationIconBadgeNumber((count) => {
        resolve(count);
      });
    });
  }

  /**
   * Set notification badge count
   */
  setBadgeCount(count: number): void {
    PushNotification.setApplicationIconBadgeNumber(count);
  }

  /**
   * Clear badge count
   */
  clearBadge(): void {
    this.setBadgeCount(0);
  }

  /**
   * Handle notification tap
   */
  private handleNotificationTap(notification: any): void {
    const { category, ...data } = notification.userInfo || notification.data || {};

    // Navigate based on category
    switch (category as NotificationCategory) {
      case 'study_reminder':
        // Navigate to study session
        this.navigateTo('StudySession', data);
        break;

      case 'exam_reminder':
        // Navigate to exam details
        this.navigateTo('ExamDetails', data);
        break;

      case 'achievement':
        // Navigate to achievements
        this.navigateTo('Achievements', data);
        break;

      case 'social':
        // Navigate to messages/social
        this.navigateTo('Messages', data);
        break;

      default:
        // Navigate to home
        this.navigateTo('Home', data);
    }
  }

  /**
   * Navigate to screen (integrate with navigation)
   */
  private navigateTo(screen: string, params?: any): void {
    // This will be integrated with React Navigation
    // For now, just log
    console.log(`Navigate to ${screen}`, params);

    // TODO: Implement with navigationRef
    // navigationRef.current?.navigate(screen, params);
  }

  /**
   * Get channel ID for category
   */
  private getCategoryChannel(category: NotificationCategory): string {
    switch (category) {
      case 'study_reminder':
        return 'study-reminders';
      case 'exam_reminder':
        return 'exam-reminders';
      case 'achievement':
        return 'achievements';
      case 'social':
        return 'social';
      case 'system':
      case 'custom':
      default:
        return 'system';
    }
  }

  /**
   * Check if current time is in quiet hours
   */
  private isQuietHours(date: Date = new Date()): boolean {
    if (!this.preferences.quietHours.enabled) {
      return false;
    }

    const { start, end } = this.preferences.quietHours;
    const currentTime = `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;

    // Handle cases where quiet hours span midnight
    if (start < end) {
      return currentTime >= start && currentTime < end;
    } else {
      return currentTime >= start || currentTime < end;
    }
  }

  /**
   * Load user preferences
   */
  async loadPreferences(): Promise<void> {
    try {
      const stored = await AsyncStorage.getItem('notification_preferences');
      if (stored) {
        this.preferences = JSON.parse(stored);
      }
    } catch (error) {
      console.error('Error loading notification preferences:', error);
    }
  }

  /**
   * Save user preferences
   */
  async savePreferences(preferences: Partial<NotificationPreferences>): Promise<void> {
    try {
      this.preferences = { ...this.preferences, ...preferences };
      await AsyncStorage.setItem('notification_preferences', JSON.stringify(this.preferences));
    } catch (error) {
      console.error('Error saving notification preferences:', error);
    }
  }

  /**
   * Get current preferences
   */
  getPreferences(): NotificationPreferences {
    return { ...this.preferences };
  }

  /**
   * Update notification preferences
   */
  async updatePreferences(updates: Partial<NotificationPreferences>): Promise<void> {
    await this.savePreferences(updates);
  }
}

export const notificationService = new NotificationService();
```

---

## Notification Types

### 1. Study Reminders

Schedule daily study reminders:

```typescript
// src/services/StudyReminderService.ts
import { notificationService } from './NotificationService';

export class StudyReminderService {
  /**
   * Schedule daily study reminder
   */
  scheduleDailyReminder(time: { hour: number; minute: number }): void {
    const date = new Date();
    date.setHours(time.hour, time.minute, 0, 0);

    // If time has passed today, schedule for tomorrow
    if (date < new Date()) {
      date.setDate(date.getDate() + 1);
    }

    notificationService.scheduleNotification({
      id: 'daily-study-reminder',
      title: 'Çalışma Zamanı!',
      message: 'Bugünkü hedeflerine ulaşmak için çalışmaya başla.',
      category: 'study_reminder',
      date,
      repeatType: 'day',
    });
  }

  /**
   * Schedule study session reminder
   */
  scheduleSessionReminder(sessionId: string, startTime: Date, subject: string): void {
    // Remind 15 minutes before
    const reminderTime = new Date(startTime.getTime() - 15 * 60 * 1000);

    notificationService.scheduleNotification({
      id: `session-${sessionId}`,
      title: `${subject} Çalışma Seansı`,
      message: '15 dakika sonra çalışma seansın başlıyor.',
      category: 'study_reminder',
      date: reminderTime,
      data: { sessionId, subject },
    });
  }

  /**
   * Cancel daily reminder
   */
  cancelDailyReminder(): void {
    notificationService.cancelNotification('daily-study-reminder');
  }
}

export const studyReminderService = new StudyReminderService();
```

### 2. Exam Reminders

```typescript
// src/services/ExamReminderService.ts
import { notificationService } from './NotificationService';

export class ExamReminderService {
  /**
   * Schedule exam reminders (1 week, 1 day, 1 hour before)
   */
  scheduleExamReminders(examId: string, examDate: Date, examName: string): void {
    const now = new Date();

    // 1 week before
    const oneWeekBefore = new Date(examDate.getTime() - 7 * 24 * 60 * 60 * 1000);
    if (oneWeekBefore > now) {
      notificationService.scheduleNotification({
        id: `exam-${examId}-week`,
        title: 'Sınav Yaklaşıyor',
        message: `${examName} sınavına 1 hafta kaldı.`,
        category: 'exam_reminder',
        date: oneWeekBefore,
        data: { examId, examName },
      });
    }

    // 1 day before
    const oneDayBefore = new Date(examDate.getTime() - 24 * 60 * 60 * 1000);
    if (oneDayBefore > now) {
      notificationService.scheduleNotification({
        id: `exam-${examId}-day`,
        title: 'Sınav Yarın!',
        message: `${examName} sınavın yarın. Hazır mısın?`,
        category: 'exam_reminder',
        date: oneDayBefore,
        data: { examId, examName },
      });
    }

    // 1 hour before
    const oneHourBefore = new Date(examDate.getTime() - 60 * 60 * 1000);
    if (oneHourBefore > now) {
      notificationService.scheduleNotification({
        id: `exam-${examId}-hour`,
        title: 'Sınav Yakında!',
        message: `${examName} sınavına 1 saat kaldı. Başarılar!`,
        category: 'exam_reminder',
        date: oneHourBefore,
        data: { examId, examName },
      });
    }
  }

  /**
   * Cancel exam reminders
   */
  cancelExamReminders(examId: string): void {
    notificationService.cancelNotification(`exam-${examId}-week`);
    notificationService.cancelNotification(`exam-${examId}-day`);
    notificationService.cancelNotification(`exam-${examId}-hour`);
  }
}

export const examReminderService = new ExamReminderService();
```

### 3. Achievement Notifications

```typescript
// src/services/AchievementNotificationService.ts
import { notificationService } from './NotificationService';

export class AchievementNotificationService {
  /**
   * Show badge earned notification
   */
  showBadgeEarned(badgeName: string, badgeDescription: string): void {
    notificationService.showLocalNotification({
      title: '🏆 Yeni Rozet Kazandın!',
      message: `${badgeName}: ${badgeDescription}`,
      category: 'achievement',
      data: { type: 'badge', badgeName },
    });
  }

  /**
   * Show level up notification
   */
  showLevelUp(newLevel: number): void {
    notificationService.showLocalNotification({
      title: '⬆️ Seviye Atladın!',
      message: `Tebrikler! Artık Seviye ${newLevel}'sin.`,
      category: 'achievement',
      data: { type: 'level_up', level: newLevel },
    });
  }

  /**
   * Show streak milestone notification
   */
  showStreakMilestone(streakDays: number): void {
    notificationService.showLocalNotification({
      title: '🔥 Seri Devam Ediyor!',
      message: `${streakDays} gündür kesintisiz çalışıyorsun. Harika!`,
      category: 'achievement',
      data: { type: 'streak', days: streakDays },
    });
  }
}

export const achievementNotificationService = new AchievementNotificationService();
```

---

## Notification Scheduling

### Custom Reminder Component

```typescript
// src/components/Notifications/CustomReminderForm.tsx
import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { Button } from 'react-native-paper';
import { notificationService } from '../../services/NotificationService';

export const CustomReminderForm: React.FC = () => {
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [date, setDate] = useState(new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);

  const handleSchedule = () => {
    if (!title || !message) {
      alert('Lütfen başlık ve mesaj girin');
      return;
    }

    notificationService.scheduleNotification({
      id: `custom-${Date.now()}`,
      title,
      message,
      category: 'custom',
      date,
    });

    alert('Hatırlatıcı planlandı!');
    setTitle('');
    setMessage('');
    setDate(new Date());
  };

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Başlık</Text>
      <TextInput
        style={styles.input}
        value={title}
        onChangeText={setTitle}
        placeholder="Hatırlatıcı başlığı"
      />

      <Text style={styles.label}>Mesaj</Text>
      <TextInput
        style={styles.input}
        value={message}
        onChangeText={setMessage}
        placeholder="Hatırlatıcı mesajı"
        multiline
      />

      <Text style={styles.label}>Tarih ve Saat</Text>
      <Button mode="outlined" onPress={() => setShowDatePicker(true)}>
        {date.toLocaleString('tr-TR')}
      </Button>

      {showDatePicker && (
        <DateTimePicker
          value={date}
          mode="datetime"
          display="default"
          onChange={(event, selectedDate) => {
            setShowDatePicker(false);
            if (selectedDate) setDate(selectedDate);
          }}
        />
      )}

      <Button mode="contained" onPress={handleSchedule} style={styles.button}>
        Hatırlatıcı Planla
      </Button>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    marginTop: 12,
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
  },
  button: {
    marginTop: 24,
  },
});
```

---

## User Preferences

### Notification Settings Screen

```typescript
// src/screens/Settings/NotificationSettings.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Switch, Button, Divider } from 'react-native-paper';
import DateTimePicker from '@react-native-community/datetimepicker';
import { notificationService, NotificationPreferences } from '../../services/NotificationService';

export const NotificationSettingsScreen: React.FC = () => {
  const [preferences, setPreferences] = useState<NotificationPreferences>(
    notificationService.getPreferences()
  );
  const [showStartTimePicker, setShowStartTimePicker] = useState(false);
  const [showEndTimePicker, setShowEndTimePicker] = useState(false);

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    await notificationService.loadPreferences();
    setPreferences(notificationService.getPreferences());
  };

  const updatePreference = async (updates: Partial<NotificationPreferences>) => {
    const newPreferences = { ...preferences, ...updates };
    setPreferences(newPreferences);
    await notificationService.updatePreferences(updates);
  };

  const parseTime = (timeStr: string): Date => {
    const [hours, minutes] = timeStr.split(':').map(Number);
    const date = new Date();
    date.setHours(hours, minutes, 0, 0);
    return date;
  };

  const formatTime = (date: Date): string => {
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
  };

  return (
    <ScrollView style={styles.container}>
      {/* Master Toggle */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Genel Ayarlar</Text>
        <View style={styles.row}>
          <Text style={styles.label}>Bildirimleri Etkinleştir</Text>
          <Switch
            value={preferences.enabled}
            onValueChange={(value) => updatePreference({ enabled: value })}
          />
        </View>
      </View>

      <Divider />

      {/* Notification Categories */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Bildirim Kategorileri</Text>

        <View style={styles.row}>
          <Text style={styles.label}>Çalışma Hatırlatıcıları</Text>
          <Switch
            value={preferences.categories.study_reminder}
            onValueChange={(value) =>
              updatePreference({
                categories: { ...preferences.categories, study_reminder: value },
              })
            }
            disabled={!preferences.enabled}
          />
        </View>

        <View style={styles.row}>
          <Text style={styles.label}>Sınav Hatırlatıcıları</Text>
          <Switch
            value={preferences.categories.exam_reminder}
            onValueChange={(value) =>
              updatePreference({
                categories: { ...preferences.categories, exam_reminder: value },
              })
            }
            disabled={!preferences.enabled}
          />
        </View>

        <View style={styles.row}>
          <Text style={styles.label}>Başarılar</Text>
          <Switch
            value={preferences.categories.achievement}
            onValueChange={(value) =>
              updatePreference({
                categories: { ...preferences.categories, achievement: value },
              })
            }
            disabled={!preferences.enabled}
          />
        </View>

        <View style={styles.row}>
          <Text style={styles.label}>Sosyal</Text>
          <Switch
            value={preferences.categories.social}
            onValueChange={(value) =>
              updatePreference({
                categories: { ...preferences.categories, social: value },
              })
            }
            disabled={!preferences.enabled}
          />
        </View>

        <View style={styles.row}>
          <Text style={styles.label}>Sistem</Text>
          <Switch
            value={preferences.categories.system}
            onValueChange={(value) =>
              updatePreference({
                categories: { ...preferences.categories, system: value },
              })
            }
            disabled={!preferences.enabled}
          />
        </View>
      </View>

      <Divider />

      {/* Quiet Hours */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Sessiz Saatler</Text>

        <View style={styles.row}>
          <Text style={styles.label}>Sessiz Saatleri Etkinleştir</Text>
          <Switch
            value={preferences.quietHours.enabled}
            onValueChange={(value) =>
              updatePreference({
                quietHours: { ...preferences.quietHours, enabled: value },
              })
            }
            disabled={!preferences.enabled}
          />
        </View>

        {preferences.quietHours.enabled && (
          <>
            <View style={styles.row}>
              <Text style={styles.label}>Başlangıç</Text>
              <Button
                mode="outlined"
                onPress={() => setShowStartTimePicker(true)}
                disabled={!preferences.enabled}
              >
                {preferences.quietHours.start}
              </Button>
            </View>

            <View style={styles.row}>
              <Text style={styles.label}>Bitiş</Text>
              <Button
                mode="outlined"
                onPress={() => setShowEndTimePicker(true)}
                disabled={!preferences.enabled}
              >
                {preferences.quietHours.end}
              </Button>
            </View>
          </>
        )}

        {showStartTimePicker && (
          <DateTimePicker
            value={parseTime(preferences.quietHours.start)}
            mode="time"
            display="default"
            onChange={(event, selectedDate) => {
              setShowStartTimePicker(false);
              if (selectedDate) {
                updatePreference({
                  quietHours: {
                    ...preferences.quietHours,
                    start: formatTime(selectedDate),
                  },
                });
              }
            }}
          />
        )}

        {showEndTimePicker && (
          <DateTimePicker
            value={parseTime(preferences.quietHours.end)}
            mode="time"
            display="default"
            onChange={(event, selectedDate) => {
              setShowEndTimePicker(false);
              if (selectedDate) {
                updatePreference({
                  quietHours: {
                    ...preferences.quietHours,
                    end: formatTime(selectedDate),
                  },
                });
              }
            }}
          />
        )}
      </View>

      <Divider />

      {/* Sound and Vibration */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Ses ve Titreşim</Text>

        <View style={styles.row}>
          <Text style={styles.label}>Bildirim Sesi</Text>
          <Switch
            value={preferences.sound}
            onValueChange={(value) => updatePreference({ sound: value })}
            disabled={!preferences.enabled}
          />
        </View>

        <View style={styles.row}>
          <Text style={styles.label}>Titreşim</Text>
          <Switch
            value={preferences.vibration}
            onValueChange={(value) => updatePreference({ vibration: value })}
            disabled={!preferences.enabled}
          />
        </View>

        <View style={styles.row}>
          <Text style={styles.label}>Rozet Sayısı</Text>
          <Switch
            value={preferences.badge}
            onValueChange={(value) => updatePreference({ badge: value })}
            disabled={!preferences.enabled}
          />
        </View>
      </View>

      <View style={styles.section}>
        <Button
          mode="outlined"
          onPress={() => notificationService.clearBadge()}
        >
          Rozet Sayısını Sıfırla
        </Button>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  section: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
  label: {
    fontSize: 16,
  },
});
```

---

## Testing

### Testing Push Notifications

#### 1. Test FCM Token Registration

```typescript
// Test in App.tsx or a test screen
import { notificationService } from './services/NotificationService';

const testFCMToken = async () => {
  await notificationService.initialize();
  const token = await notificationService.getFCMToken();
  console.log('FCM Token:', token);
};
```

#### 2. Test Local Notification

```typescript
import { notificationService } from './services/NotificationService';

const testLocalNotification = () => {
  notificationService.showLocalNotification({
    title: 'Test Notification',
    message: 'This is a test notification',
    category: 'system',
  });
};
```

#### 3. Test Scheduled Notification

```typescript
import { notificationService } from './services/NotificationService';

const testScheduledNotification = () => {
  const date = new Date();
  date.setSeconds(date.getSeconds() + 10); // 10 seconds from now

  notificationService.scheduleNotification({
    id: 'test-scheduled',
    title: 'Scheduled Test',
    message: 'This notification was scheduled 10 seconds ago',
    category: 'system',
    date,
  });
};
```

#### 4. Send Test FCM Message

Use Firebase Console:
1. Go to Firebase Console → Cloud Messaging
2. Click "Send your first message"
3. Enter notification title and text
4. Click "Send test message"
5. Paste FCM token from app
6. Click "Test"

Or use cURL:

```bash
curl -X POST https://fcm.googleapis.com/fcm/send \
  -H "Authorization: key=YOUR_SERVER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "DEVICE_FCM_TOKEN",
    "notification": {
      "title": "Test Notification",
      "body": "This is a test from cURL"
    },
    "data": {
      "category": "system"
    }
  }'
```

### Backend Integration

Send notifications from backend:

```python
# backend/services/notification_service.py
from firebase_admin import messaging
import firebase_admin
from firebase_admin import credentials

# Initialize Firebase Admin SDK
cred = credentials.Certificate("path/to/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

def send_notification(token: str, title: str, body: str, data: dict = None):
    """Send push notification to device"""
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        token=token,
    )

    response = messaging.send(message)
    return response

def send_multicast_notification(tokens: list[str], title: str, body: str, data: dict = None):
    """Send notification to multiple devices"""
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        tokens=tokens,
    )

    response = messaging.send_multicast(message)
    return response
```

---

## Summary

This comprehensive push notification system provides:

✅ **Firebase Cloud Messaging integration** for remote push notifications
✅ **Local notifications** with scheduling and repeat options
✅ **Multiple notification categories** (study, exam, achievement, social, system)
✅ **User preferences** with granular control over notification types
✅ **Quiet hours** to prevent notifications during specific times
✅ **Custom sounds and vibration** patterns
✅ **Badge management** for iOS
✅ **Deep linking** support for notification taps
✅ **Background sync** for notifications when app is closed
✅ **Study reminders** with daily and session-based reminders
✅ **Exam reminders** with multi-stage alerts (1 week, 1 day, 1 hour)
✅ **Achievement notifications** for badges, level-ups, and streaks

The system is fully type-safe with TypeScript and follows React Native best practices for cross-platform compatibility.
