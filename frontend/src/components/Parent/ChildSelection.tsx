import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Plus, 
  Users, 
  Mail, 
  Clock, 
  CheckCircle, 
  XCircle,
  AlertCircle,
  UserPlus
} from 'lucide-react';
import { parentService } from '@/services/parentService';
import { LoadingSpinner } from '@/components/Common/LoadingSpinner';

interface ChildRelation {
  id: number;
  parent_id: number;
  child_id: number;
  child_name: string;
  child_email: string;
  relation_type: string;
  approved: boolean;
  created_at: string;
  approved_at?: string;
}

export const ChildSelection: React.FC = () => {
  const [children, setChildren] = useState<ChildRelation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [addingChild, setAddingChild] = useState(false);
  const [newChildEmail, setNewChildEmail] = useState('');
  const [relationType, setRelationType] = useState('parent');

  useEffect(() => {
    loadChildren();
  }, []);

  const loadChildren = async () => {
    try {
      setLoading(true);
      const data = await parentService.getChildren();
      setChildren(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Çocuk listesi yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleAddChild = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newChildEmail.trim()) {
      setError('Email adresi gereklidir');
      return;
    }

    try {
      setAddingChild(true);
      await parentService.createChildRelation({
        child_email: newChildEmail.trim(),
        relation_type: relationType
      });
      
      setNewChildEmail('');
      setShowAddForm(false);
      setError(null);
      await loadChildren();
    } catch (err: any) {
      setError(err.message || 'Çocuk eklenirken hata oluştu');
    } finally {
      setAddingChild(false);
    }
  };

  const getStatusBadge = (relation: ChildRelation) => {
    if (relation.approved) {
      return (
        <Badge className="bg-green-100 text-green-800">
          <CheckCircle className="h-3 w-3 mr-1" />
          Onaylandı
        </Badge>
      );
    } else {
      return (
        <Badge className="bg-yellow-100 text-yellow-800">
          <Clock className="h-3 w-3 mr-1" />
          Onay Bekliyor
        </Badge>
      );
    }
  };

  const getRelationTypeText = (type: string) => {
    switch (type) {
      case 'parent':
        return 'Veli';
      case 'guardian':
        return 'Vasi';
      default:
        return type;
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Çocuk Seçimi ve Yönetimi</h2>
        <Button 
          onClick={() => setShowAddForm(!showAddForm)}
          className="flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Çocuk Ekle
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      {/* Add Child Form */}
      {showAddForm && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserPlus className="h-5 w-5" />
              Yeni Çocuk Ekle
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAddChild} className="space-y-4">
              <div>
                <Label htmlFor="childEmail">Çocuğun Email Adresi</Label>
                <Input
                  id="childEmail"
                  type="email"
                  value={newChildEmail}
                  onChange={(e) => setNewChildEmail(e.target.value)}
                  placeholder="ornek@email.com"
                  required
                />
                <p className="text-sm text-gray-600 mt-1">
                  Çocuğunuzun platformda kayıtlı email adresini girin. 
                  Çocuğunuz bu isteği onaylamalıdır.
                </p>
              </div>

              <div>
                <Label htmlFor="relationType">İlişki Türü</Label>
                <select
                  id="relationType"
                  value={relationType}
                  onChange={(e) => setRelationType(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="parent">Veli</option>
                  <option value="guardian">Vasi</option>
                </select>
              </div>

              <div className="flex gap-2">
                <Button 
                  type="submit" 
                  disabled={addingChild}
                  className="flex items-center gap-2"
                >
                  {addingChild ? (
                    <LoadingSpinner size="sm" />
                  ) : (
                    <Plus className="h-4 w-4" />
                  )}
                  Ekle
                </Button>
                <Button 
                  type="button" 
                  variant="outline"
                  onClick={() => {
                    setShowAddForm(false);
                    setNewChildEmail('');
                    setError(null);
                  }}
                >
                  İptal
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Children List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Çocuklarım ({children.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {children.length === 0 ? (
            <div className="text-center py-8">
              <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 mb-2">Henüz çocuk eklenmemiş</p>
              <p className="text-sm text-gray-400">
                Çocuğunuzun email adresini kullanarak takip isteği gönderebilirsiniz
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {children.map((child) => (
                <div
                  key={child.id}
                  className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-semibold text-lg">{child.child_name}</h3>
                      <div className="flex items-center gap-2 text-sm text-gray-600 mt-1">
                        <Mail className="h-4 w-4" />
                        <span>{child.child_email}</span>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      {getStatusBadge(child)}
                      <Badge variant="outline">
                        {getRelationTypeText(child.relation_type)}
                      </Badge>
                    </div>
                  </div>

                  <div className="flex justify-between items-center text-sm text-gray-600">
                    <div>
                      <p>İstek Tarihi: {new Date(child.created_at).toLocaleDateString('tr-TR')}</p>
                      {child.approved_at && (
                        <p>Onay Tarihi: {new Date(child.approved_at).toLocaleDateString('tr-TR')}</p>
                      )}
                    </div>
                    
                    {child.approved && (
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => {
                          // Navigate to child performance page
                          window.location.href = `/parent/child/${child.child_id}/performance`;
                        }}
                      >
                        Performansı Görüntüle
                      </Button>
                    )}
                  </div>

                  {!child.approved && (
                    <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                      <div className="flex items-center gap-2 text-yellow-800">
                        <Clock className="h-4 w-4" />
                        <span className="text-sm font-medium">
                          Çocuğunuzun onayı bekleniyor
                        </span>
                      </div>
                      <p className="text-xs text-yellow-700 mt-1">
                        Çocuğunuz bu isteği onayladığında performans verilerini görüntüleyebileceksiniz.
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-blue-900 mb-2">Önemli Bilgiler</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Çocuğunuz platformda kayıtlı olmalıdır</li>
                <li>• Takip isteğiniz çocuğunuz tarafından onaylanmalıdır</li>
                <li>• Onay sonrası tüm performans verilerini görüntüleyebilirsiniz</li>
                <li>• Haftalık raporlar otomatik olarak oluşturulur</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};