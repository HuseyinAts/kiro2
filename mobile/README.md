# Kiro Mobile App - React Native

**Task 110: React Native Setup**

Complete React Native mobile application for iOS and Android.

## Table of Contents

- [Project Setup](#project-setup)
- [Folder Structure](#folder-structure)
- [Navigation](#navigation)
- [State Management](#state-management)
- [API Integration](#api-integration)
- [Development](#development)
- [Build & Deploy](#build--deploy)

---

## Project Setup

### Prerequisites

```bash
# Node.js 18+ and npm/yarn
node --version  # v18+
npm --version   # 9+

# React Native CLI
npm install -g react-native-cli

# iOS (macOS only)
pod --version  # CocoaPods for iOS dependencies

# Android
# Android Studio with SDK Platform 33+
# ANDROID_HOME environment variable set
```

### Installation

```bash
# Initialize React Native project
npx react-native init KiroMobile --template react-native-template-typescript

cd KiroMobile

# Install dependencies
npm install

# Install navigation
npm install @react-navigation/native @react-navigation/stack @react-navigation/bottom-tabs
npm install react-native-screens react-native-safe-area-context
npm install react-native-gesture-handler react-native-reanimated

# Install state management (Redux Toolkit)
npm install @reduxjs/toolkit react-redux
npm install redux-persist @react-native-async-storage/async-storage

# Install API & networking
npm install axios
npm install @tanstack/react-query

# Install UI components
npm install react-native-vector-icons
npm install react-native-paper  # Material Design

# Install utilities
npm install react-native-dotenv
npm install react-native-fast-image  # Optimized images
npm install date-fns  # Date utilities

# iOS specific
cd ios && pod install && cd ..
```

### Configuration

#### Environment Variables

Create `.env` file:

```env
API_URL=http://localhost:8000
API_TIMEOUT=30000
ENABLE_LOGGING=true
```

---

## Folder Structure

### Task 110.1: Project Structure

```
mobile/
├── src/
│   ├── api/                    # API integration
│   │   ├── client.ts           # Axios client configuration
│   │   ├── endpoints.ts        # API endpoints
│   │   ├── auth.api.ts         # Authentication API
│   │   ├── questions.api.ts    # Questions API
│   │   ├── study.api.ts        # Study rooms API
│   │   └── teachers.api.ts     # Teacher pool API
│   │
│   ├── assets/                 # Images, fonts, icons
│   │   ├── images/
│   │   ├── icons/
│   │   └── fonts/
│   │
│   ├── components/             # Reusable components
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Loading.tsx
│   │   │   └── ErrorBoundary.tsx
│   │   ├── questions/
│   │   │   ├── QuestionCard.tsx
│   │   │   ├── QuestionList.tsx
│   │   │   └── AnswerOptions.tsx
│   │   └── navigation/
│   │       ├── TabBar.tsx
│   │       └── Header.tsx
│   │
│   ├── navigation/             # Navigation setup
│   │   ├── RootNavigator.tsx   # Main navigator
│   │   ├── AuthStack.tsx       # Authentication screens
│   │   ├── MainStack.tsx       # Main app screens
│   │   ├── TabNavigator.tsx    # Bottom tabs
│   │   └── types.ts            # Navigation types
│   │
│   ├── screens/                # Screen components
│   │   ├── auth/
│   │   │   ├── LoginScreen.tsx
│   │   │   ├── RegisterScreen.tsx
│   │   │   └── ForgotPasswordScreen.tsx
│   │   ├── home/
│   │   │   ├── HomeScreen.tsx
│   │   │   └── DashboardScreen.tsx
│   │   ├── questions/
│   │   │   ├── QuestionBankScreen.tsx
│   │   │   ├── QuestionDetailScreen.tsx
│   │   │   └── PracticeScreen.tsx
│   │   ├── study/
│   │   │   ├── StudyRoomsScreen.tsx
│   │   │   └── StudyRoomDetailScreen.tsx
│   │   ├── teachers/
│   │   │   ├── TeacherListScreen.tsx
│   │   │   └── TeacherProfileScreen.tsx
│   │   └── profile/
│   │       ├── ProfileScreen.tsx
│   │       └── SettingsScreen.tsx
│   │
│   ├── store/                  # Redux store
│   │   ├── index.ts            # Store configuration
│   │   ├── slices/
│   │   │   ├── authSlice.ts
│   │   │   ├── userSlice.ts
│   │   │   ├── questionsSlice.ts
│   │   │   └── studySlice.ts
│   │   └── hooks.ts            # Typed hooks
│   │
│   ├── hooks/                  # Custom hooks
│   │   ├── useAuth.ts
│   │   ├── useQuestions.ts
│   │   ├── useStudyRooms.ts
│   │   └── useTeachers.ts
│   │
│   ├── utils/                  # Utility functions
│   │   ├── storage.ts          # AsyncStorage helpers
│   │   ├── validators.ts       # Form validation
│   │   ├── formatters.ts       # Data formatters
│   │   └── constants.ts        # App constants
│   │
│   ├── types/                  # TypeScript types
│   │   ├── auth.types.ts
│   │   ├── question.types.ts
│   │   ├── study.types.ts
│   │   └── api.types.ts
│   │
│   ├── theme/                  # App theming
│   │   ├── colors.ts
│   │   ├── typography.ts
│   │   ├── spacing.ts
│   │   └── index.ts
│   │
│   └── App.tsx                 # Root component
│
├── android/                    # Android native code
├── ios/                        # iOS native code
├── __tests__/                  # Unit tests
├── .env                        # Environment variables
├── .eslintrc.js               # ESLint config
├── .prettierrc.js             # Prettier config
├── tsconfig.json              # TypeScript config
├── package.json
└── README.md
```

---

## Navigation

### Task 110.2: React Navigation Setup

#### Root Navigator (`src/navigation/RootNavigator.tsx`)

```typescript
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { useAppSelector } from '../store/hooks';

import AuthStack from './AuthStack';
import MainStack from './MainStack';
import { RootStackParamList } from './types';

const Stack = createStackNavigator<RootStackParamList>();

export const RootNavigator: React.FC = () => {
  const { isAuthenticated } = useAppSelector(state => state.auth);

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {isAuthenticated ? (
          <Stack.Screen name="Main" component={MainStack} />
        ) : (
          <Stack.Screen name="Auth" component={AuthStack} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};
```

#### Auth Stack (`src/navigation/AuthStack.tsx`)

```typescript
import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { AuthStackParamList } from './types';

import LoginScreen from '../screens/auth/LoginScreen';
import RegisterScreen from '../screens/auth/RegisterScreen';
import ForgotPasswordScreen from '../screens/auth/ForgotPasswordScreen';

const Stack = createStackNavigator<AuthStackParamList>();

const AuthStack: React.FC = () => {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: '#3b82f6' },
        headerTintColor: '#fff',
      }}
    >
      <Stack.Screen
        name="Login"
        component={LoginScreen}
        options={{ title: 'Giriş Yap' }}
      />
      <Stack.Screen
        name="Register"
        component={RegisterScreen}
        options={{ title: 'Kayıt Ol' }}
      />
      <Stack.Screen
        name="ForgotPassword"
        component={ForgotPasswordScreen}
        options={{ title: 'Şifremi Unuttum' }}
      />
    </Stack.Navigator>
  );
};

export default AuthStack;
```

#### Tab Navigator (`src/navigation/TabNavigator.tsx`)

```typescript
import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import HomeScreen from '../screens/home/HomeScreen';
import QuestionBankScreen from '../screens/questions/QuestionBankScreen';
import StudyRoomsScreen from '../screens/study/StudyRoomsScreen';
import TeacherListScreen from '../screens/teachers/TeacherListScreen';
import ProfileScreen from '../screens/profile/ProfileScreen';

const Tab = createBottomTabNavigator();

const TabNavigator: React.FC = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ color, size }) => {
          let iconName = 'home';

          switch (route.name) {
            case 'Home': iconName = 'home'; break;
            case 'Questions': iconName = 'book-open-variant'; break;
            case 'StudyRooms': iconName = 'account-group'; break;
            case 'Teachers': iconName = 'teach'; break;
            case 'Profile': iconName = 'account'; break;
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#3b82f6',
        tabBarInactiveTintColor: '#6b7280',
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} options={{ title: 'Ana Sayfa' }} />
      <Tab.Screen name="Questions" component={QuestionBankScreen} options={{ title: 'Sorular' }} />
      <Tab.Screen name="StudyRooms" component={StudyRoomsScreen} options={{ title: 'Çalışma Odaları' }} />
      <Tab.Screen name="Teachers" component={TeacherListScreen} options={{ title: 'Öğretmenler' }} />
      <Tab.Screen name="Profile" component={ProfileScreen} options={{ title: 'Profil' }} />
    </Tab.Navigator>
  );
};

export default TabNavigator;
```

#### Navigation Types (`src/navigation/types.ts`)

```typescript
export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
};

export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
};

export type MainStackParamList = {
  Tabs: undefined;
  QuestionDetail: { questionId: string };
  StudyRoomDetail: { roomId: string };
  TeacherProfile: { teacherId: string };
};

export type TabParamList = {
  Home: undefined;
  Questions: undefined;
  StudyRooms: undefined;
  Teachers: undefined;
  Profile: undefined;
};
```

#### Deep Linking Configuration

```typescript
// In App.tsx or RootNavigator
const linking = {
  prefixes: ['kiro://', 'https://kiro.app'],
  config: {
    screens: {
      Main: {
        screens: {
          QuestionDetail: 'questions/:questionId',
          StudyRoomDetail: 'rooms/:roomId',
          TeacherProfile: 'teachers/:teacherId',
        },
      },
    },
  },
};

<NavigationContainer linking={linking}>
  {/* ... */}
</NavigationContainer>
```

---

## State Management

### Task 110.3: Redux Toolkit Setup

#### Store Configuration (`src/store/index.ts`)

```typescript
import { configureStore } from '@reduxjs/toolkit';
import { persistStore, persistReducer } from 'redux-persist';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { combineReducers } from 'redux';

import authReducer from './slices/authSlice';
import userReducer from './slices/userSlice';
import questionsReducer from './slices/questionsSlice';
import studyReducer from './slices/studySlice';

const persistConfig = {
  key: 'root',
  storage: AsyncStorage,
  whitelist: ['auth', 'user'], // Only persist these reducers
};

const rootReducer = combineReducers({
  auth: authReducer,
  user: userReducer,
  questions: questionsReducer,
  study: studyReducer,
});

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
});

export const persistor = persistStore(store);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

#### Auth Slice (`src/store/slices/authSlice.ts`)

```typescript
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { authAPI } from '../../api/auth.api';
import { AuthState, LoginCredentials, RegisterData } from '../../types/auth.types';

const initialState: AuthState = {
  isAuthenticated: false,
  token: null,
  user: null,
  loading: false,
  error: null,
};

export const login = createAsyncThunk(
  'auth/login',
  async (credentials: LoginCredentials, { rejectWithValue }) => {
    try {
      const response = await authAPI.login(credentials);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data || 'Login failed');
    }
  }
);

export const register = createAsyncThunk(
  'auth/register',
  async (data: RegisterData, { rejectWithValue }) => {
    try {
      const response = await authAPI.register(data);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data || 'Registration failed');
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      state.isAuthenticated = false;
      state.token = null;
      state.user = null;
    },
    setCredentials: (state, action: PayloadAction<{ token: string; user: any }>) => {
      state.isAuthenticated = true;
      state.token = action.payload.token;
      state.user = action.payload.user;
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.token = action.payload.token;
        state.user = action.payload.user;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Register
      .addCase(register.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.token = action.payload.token;
        state.user = action.payload.user;
      })
      .addCase(register.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { logout, setCredentials } = authSlice.actions;
export default authSlice.reducer;
```

#### Typed Hooks (`src/store/hooks.ts`)

```typescript
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from './index';

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
```

---

## API Integration

### Task 110.4: API Client Setup

#### API Client (`src/api/client.ts`)

```typescript
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_URL, API_TIMEOUT } from '@env';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL || 'http://localhost:8000',
      timeout: Number(API_TIMEOUT) || 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor - Add auth token
    this.client.interceptors.request.use(
      async (config) => {
        const token = await AsyncStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - Handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Unauthorized - clear auth and redirect to login
          await AsyncStorage.removeItem('auth_token');
          // Trigger logout action
        }
        return Promise.reject(error);
      }
    );
  }

  public get<T>(url: string, config?: AxiosRequestConfig) {
    return this.client.get<T>(url, config);
  }

  public post<T>(url: string, data?: any, config?: AxiosRequestConfig) {
    return this.client.post<T>(url, data, config);
  }

  public put<T>(url: string, data?: any, config?: AxiosRequestConfig) {
    return this.client.put<T>(url, data, config);
  }

  public delete<T>(url: string, config?: AxiosRequestConfig) {
    return this.client.delete<T>(url, config);
  }
}

export const apiClient = new APIClient();
```

#### Auth API (`src/api/auth.api.ts`)

```typescript
import { apiClient } from './client';
import { LoginCredentials, RegisterData, AuthResponse } from '../types/auth.types';

export const authAPI = {
  login: (credentials: LoginCredentials) =>
    apiClient.post<AuthResponse>('/api/auth/login', credentials),

  register: (data: RegisterData) =>
    apiClient.post<AuthResponse>('/api/auth/register', data),

  logout: () =>
    apiClient.post('/api/auth/logout'),

  refreshToken: () =>
    apiClient.post<{ token: string }>('/api/auth/refresh'),

  forgotPassword: (email: string) =>
    apiClient.post('/api/auth/forgot-password', { email }),

  resetPassword: (token: string, password: string) =>
    apiClient.post('/api/auth/reset-password', { token, password }),
};
```

#### Questions API (`src/api/questions.api.ts`)

```typescript
import { apiClient } from './client';
import { Question, QuestionFilters } from '../types/question.types';

export const questionsAPI = {
  getQuestions: (filters?: QuestionFilters) =>
    apiClient.get<{ questions: Question[] }>('/api/questions', { params: filters }),

  getQuestionById: (id: string) =>
    apiClient.get<Question>(`/api/questions/${id}`),

  submitAnswer: (questionId: string, answer: string) =>
    apiClient.post(`/api/questions/${questionId}/answer`, { answer }),

  getMyProgress: () =>
    apiClient.get('/api/questions/my-progress'),
};
```

---

## Development

### Running the App

```bash
# Start Metro bundler
npm start

# Run on iOS
npm run ios

# Run on Android
npm run android

# Run on specific device
npm run ios -- --simulator="iPhone 14"
npm run android -- --deviceId=emulator-5554
```

### Testing

```bash
# Run unit tests
npm test

# Run with coverage
npm test -- --coverage

# Run E2E tests (with Detox)
npm run e2e:ios
npm run e2e:android
```

### Code Quality

```bash
# Lint
npm run lint

# Format
npm run format

# Type check
npm run type-check
```

---

## Build & Deploy

### iOS Build

```bash
cd ios

# Install pods
pod install

# Build
xcodebuild -workspace KiroMobile.xcworkspace \
  -scheme KiroMobile \
  -configuration Release

# Or use Xcode GUI
# Open ios/KiroMobile.xcworkspace in Xcode
# Product > Archive
```

### Android Build

```bash
cd android

# Build APK
./gradlew assembleRelease

# Build AAB (for Play Store)
./gradlew bundleRelease

# Output: android/app/build/outputs/
```

### App Distribution

```bash
# Using Fastlane
fastlane ios beta     # TestFlight
fastlane android beta # Google Play Internal Testing
```

---

## Additional Features

### Offline Support (Task 111)
- Redux Persist for state
- Local database with WatermelonDB or Realm
- Queue system for sync

### Push Notifications (Task 112)
- Firebase Cloud Messaging integration
- Notification categories
- Deep linking from notifications

### Performance
- React Native Fast Image for images
- Memoization with React.memo
- FlatList optimization
- Code splitting with lazy loading

### Security
- Keychain/Keystore for sensitive data
- Certificate pinning
- Code obfuscation
- Jailbreak/Root detection

---

## Resources

- [React Native Documentation](https://reactnative.dev/)
- [React Navigation](https://reactnavigation.org/)
- [Redux Toolkit](https://redux-toolkit.js.org/)
- [React Query](https://tanstack.com/query/latest)
