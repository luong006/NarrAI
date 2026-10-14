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
    localStorage.removeItem('user');
  },
  getUser(): { username: string; full_name?: string } | null {
    if (typeof window === 'undefined') return null;
    try {
      const raw = localStorage.getItem('user');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },
  setUser(userOrUsername: { username: string; full_name?: string } | string, fullName?: string) {
    if (typeof window === 'undefined') return;
    const userObj = typeof userOrUsername === 'string'
      ? { username: userOrUsername, full_name: fullName }
      : userOrUsername;
    localStorage.setItem('user', JSON.stringify(userObj));
  },
  clear() {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('token');
    localStorage.removeItem('narrai_token');
    localStorage.removeItem('user');
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
