export const storage = {
  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token') || localStorage.getItem('narrai_token');
  },
  setToken(token: string) {
    if (typeof window === 'undefined') return;
    localStorage.setItem('token', token);
    localStorage.setItem('narrai_token', token);
  },
  removeToken() {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('token');
    localStorage.removeItem('narrai_token');
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
