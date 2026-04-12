import { create } from 'zustand';

interface ThemeState {
  isDark: boolean;
  toggle: () => void;
}

function resolveInitialTheme() {
  const savedTheme = localStorage.getItem('theme');

  if (savedTheme === 'dark') {
    return true;
  }

  if (savedTheme === 'light') {
    return false;
  }

  if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  return false;
}

export const useThemeStore = create<ThemeState>((set) => ({
  isDark: resolveInitialTheme(),
  toggle: () => set((state) => ({ isDark: !state.isDark })),
}));
