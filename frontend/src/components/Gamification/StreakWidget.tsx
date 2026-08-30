import React from 'react';
import { Box, Typography, IconButton, Tooltip, Badge } from '@mui/material';
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment';
import AcUnitIcon from '@mui/icons-material/AcUnit'; // For freeze

interface StreakWidgetProps {
  streak: number;
  freezeCount: number;
  onFreezeBuy?: () => void;
}

export const StreakWidget: React.FC<StreakWidgetProps> = ({ streak, freezeCount, onFreezeBuy }) => {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 1, bgcolor: 'background.paper', borderRadius: 2, boxShadow: 1 }}>
      <Tooltip title={`Şu anki serin: ${streak} gün`}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <LocalFireDepartmentIcon sx={{ color: streak > 0 ? 'orange' : 'gray', fontSize: 28 }} />
          <Typography variant="h6" sx={{ fontWeight: 'bold', ml: 0.5, color: streak > 0 ? 'orange' : 'gray' }}>
            {streak}
          </Typography>
        </Box>
      </Tooltip>

      <Tooltip title={`Seri Dondurucu: ${freezeCount} adet var. (50 YksCoin karşılığında almak için tıkla)`}>
        <IconButton size="small" onClick={onFreezeBuy} color="primary">
          <Badge badgeContent={freezeCount} color="secondary">
            <AcUnitIcon sx={{ color: freezeCount > 0 ? '#4fc3f7' : 'gray' }} />
          </Badge>
        </IconButton>
      </Tooltip>
    </Box>
  );
};
