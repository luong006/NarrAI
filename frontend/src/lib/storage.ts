export const storage = {
  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token');
  },
  setToken(token: string) {
    if (typeof window === 'undefined') return;
    localStorage.setItem('token', token);
  },
  removeToken() {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('token');
  },
  getLanguage(): 'vi' | 'en' {
    if (typeof window === 'undefined') return 'vi';
    return (localStorage.getItem('language') as 'vi' | 'en') || 'vi';
  },
  setLanguage(lang: 'vi' | 'en') {
    if (typeof window === 'undefined') return;
    localStorage.setItem('language', lang);
  },
};
