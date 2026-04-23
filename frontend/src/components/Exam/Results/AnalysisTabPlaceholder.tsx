import { Alert, Typography } from '@mui/material';
import * as React from 'react';

/** Ortak metin: detaylı analiz sekmeleri API/FE paritesi ile aşamalı açılacak. */
export const AnalysisTabPlaceholder: React.FC<{ title: string }> = ({ title }) => (
  <>
    <Typography variant="h6" gutterBottom>
      {title}
    </Typography>
    <Alert severity="info">
      Bu analiz görünümü kademeli olarak etkinleştirilecek; özet metrikler sınav
      sonuç ekranında mevcut. Tam IRT / ZPD / trend arayüzleri backend verisiyle
      eşlenince güncellenecek.
    </Alert>
  </>
);
