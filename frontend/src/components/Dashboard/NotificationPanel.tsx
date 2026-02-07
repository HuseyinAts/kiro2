import {
  Notifications,
  CheckCircle,
  Warning,
  Info,
  Error,
  Close as _Close,
  MarkEmailRead,
  Delete as _Delete,
  Refresh,
  NotificationsActive,
  NotificationsOff,
} from '@mui/icons-material';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Typography,
  Chip,
  IconButton,
  Badge,
  Box,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Divider,
  Card as _Card,
  CardContent as _CardContent,
} from '@mui/material';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { getNotifications, markNotificationAsRead } from '../../api';
import { Notification } from '../../types';
import { dateUtils } from '@/utils/dateUtils';

interface NotificationPanelProps {
  open: boolean
  onClose: () => void
}

export function NotificationPanel({ open, onClose }: NotificationPanelProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [markingAsRead, setMarkingAsRead] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      loadNotifications();
    }
  }, [open]);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      setError(null);
      const notificationsData = await getNotifications(false, 100); // Tüm bildirimler
      setNotifications(notificationsData);
    } catch (err) {
      console.error('Bildirimler yüklenirken hata:', err);
      setError('Bildirimler yüklenirken bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      setMarkingAsRead(notificationId);
      await markNotificationAsRead(notificationId);

      // Local state'i güncelle
      setNotifications(notifications.map(n =>
        n.bildirim_id === notificationId
          ? { ...n, okundu: true }
          : n,
      ));
    } catch (err) {
      console.error('Bildirim okundu olarak işaretlenirken hata:', err);
      setError('Bildirim güncellenirken bir hata oluştu');
    } finally {
      setMarkingAsRead(null);
    }
  };

  const handleMarkAllAsRead = async () => {
    const unreadNotifications = notifications.filter(n => !n.okundu);

    try {
      // Tüm okunmamış bildirimleri paralel olarak işaretle
      await Promise.all(
        unreadNotifications.map(n => markNotificationAsRead(n.bildirim_id)),
      );

      // Local state'i güncelle
      setNotifications(notifications.map(n => ({ ...n, okundu: true })));
    } catch (err) {
      console.error('Bildirimler okundu olarak işaretlenirken hata:', err);
      setError('Bildirimler güncellenirken bir hata oluştu');
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'basari':
        return <CheckCircle className="text-green-500" />;
      case 'uyari':
        return <Warning className="text-yellow-500" />;
      case 'hata':
        return <Error className="text-red-500" />;
      default:
        return <Info className="text-blue-500" />;
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'basari': return 'success';
      case 'uyari': return 'warning';
      case 'hata': return 'error';
      default: return 'info';
    }
  };

  const filterNotifications = (notifications: Notification[]) => {
    switch (activeTab) {
      case 0: // Tümü
        return notifications;
      case 1: // Okunmamış
        return notifications.filter(n => !n.okundu);
      case 2: // Başarı
        return notifications.filter(n => n.tip === 'basari');
      case 3: // Uyarı
        return notifications.filter(n => n.tip === 'uyari');
      case 4: // Hata
        return notifications.filter(n => n.tip === 'hata');
      default:
        return notifications;
    }
  };

  const filteredNotifications = filterNotifications(notifications);
  const unreadCount = notifications.filter(n => !n.okundu).length;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Badge badgeContent={unreadCount} color="error">
              <Notifications />
            </Badge>
            <Typography variant="h5">Bildirimler</Typography>
          </div>
          <div className="flex gap-2">
            {unreadCount > 0 && (
              <Button
                size="small"
                startIcon={<MarkEmailRead />}
                onClick={handleMarkAllAsRead}
              >
                Tümünü Okundu İşaretle
              </Button>
            )}
            <IconButton onClick={loadNotifications}>
              <Refresh />
            </IconButton>
          </div>
        </div>
      </DialogTitle>

      <DialogContent className="p-0">
        {error && (
          <Alert severity="error" className="m-4">
            {error}
          </Alert>
        )}

        {/* Tabs */}
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
          className="border-b"
        >
          <Tab
            label={`Tümü (${notifications.length})`}
            icon={<Notifications />}
          />
          <Tab
            label={`Okunmamış (${unreadCount})`}
            icon={<NotificationsActive />}
          />
          <Tab
            label={`Başarı (${notifications.filter(n => n.tip === 'basari').length})`}
            icon={<CheckCircle />}
          />
          <Tab
            label={`Uyarı (${notifications.filter(n => n.tip === 'uyari').length})`}
            icon={<Warning />}
          />
          <Tab
            label={`Hata (${notifications.filter(n => n.tip === 'hata').length})`}
            icon={<Error />}
          />
        </Tabs>

        {loading ? (
          <Box className="flex items-center justify-center py-8">
            <CircularProgress />
          </Box>
        ) : filteredNotifications.length === 0 ? (
          <Box className="text-center py-8">
            <NotificationsOff className="text-6xl text-gray-400 mb-4" />
            <Typography variant="h6" color="textSecondary" className="mb-2">
              {activeTab === 1 ? 'Okunmamış bildirim yok' : 'Bildirim bulunamadı'}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {activeTab === 1
                ? 'Tüm bildirimlerinizi okumuşsunuz!'
                : 'Bu kategoride henüz bildirim bulunmuyor.'
              }
            </Typography>
          </Box>
        ) : (
          <List className="p-0">
            {filteredNotifications.map((notification, index) => (
              <React.Fragment key={notification.bildirim_id}>
                <ListItem
                  className={`${!notification.okundu ? 'bg-blue-50' : ''} hover:bg-gray-50`}
                  secondaryAction={
                    <div className="flex items-center gap-1">
                      {!notification.okundu && (
                        <IconButton
                          size="small"
                          onClick={() => handleMarkAsRead(notification.bildirim_id)}
                          disabled={markingAsRead === notification.bildirim_id}
                        >
                          {markingAsRead === notification.bildirim_id ? (
                            <CircularProgress size={16} />
                          ) : (
                            <MarkEmailRead />
                          )}
                        </IconButton>
                      )}
                    </div>
                  }
                >
                  <ListItemAvatar>
                    <Avatar className={
                      notification.tip === 'basari' ? 'bg-green-100' :
                      notification.tip === 'uyari' ? 'bg-yellow-100' :
                      notification.tip === 'hata' ? 'bg-red-100' :
                      'bg-blue-100'
                    }>
                      {getNotificationIcon(notification.tip)}
                    </Avatar>
                  </ListItemAvatar>

                  <ListItemText
                    primary={
                      <div className="flex items-center gap-2 mb-1">
                        <Typography
                          variant="subtitle1"
                          className={`${!notification.okundu ? 'font-bold' : ''}`}
                        >
                          {notification.baslik}
                        </Typography>
                        <Chip
                          size="small"
                          label={notification.tip}
                          color={getNotificationColor(notification.tip) as any}
                          variant="outlined"
                        />
                        {!notification.okundu && (
                          <Badge color="primary" variant="dot" />
                        )}
                      </div>
                    }
                    secondary={
                      <div>
                        <Typography variant="body2" className="mb-1">
                          {notification.mesaj}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {dateUtils.format(notification.tarih, 'DD MMMM YYYY HH:mm')}
                        </Typography>
                        {notification.eylem_url && (
                          <Button
                            size="small"
                            variant="text"
                            className="ml-2"
                            onClick={() => {
                              // Eylem URL'sine yönlendir
                              window.location.href = notification.eylem_url!;
                            }}
                          >
                            Görüntüle
                          </Button>
                        )}
                      </div>
                    }
                  />
                </ListItem>
                {index < filteredNotifications.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Kapat</Button>
      </DialogActions>
    </Dialog>
  );
}

export default NotificationPanel;