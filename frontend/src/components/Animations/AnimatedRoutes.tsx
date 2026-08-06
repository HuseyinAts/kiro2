import { AnimatePresence } from 'framer-motion';
import { Routes, useLocation } from 'react-router-dom';

/**
 * AnimatedRoutes Component
 * Replaces react-router's <Routes> to enable exit animations using Framer Motion.
 * Only the specific matched <Route> unmounts, preserving layout state.
 */
export const AnimatedRoutes: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        {children}
      </Routes>
    </AnimatePresence>
  );
};
