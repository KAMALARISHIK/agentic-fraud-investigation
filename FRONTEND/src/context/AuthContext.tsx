import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
  email: string;
  name: string;
  role: string;
  avatarUrl?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, pass: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('fraudsight_auth_user');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return null;
      }
    }
    return null;
  });

  const isAuthenticated = !!user;

  const login = async (email: string, pass: string): Promise<boolean> => {
    // Validate credentials
    const trimmedEmail = email.trim().toLowerCase();
    if (
      (trimmedEmail === 'analyst@fraudsight.demo' || trimmedEmail === 'demo@fraudsight.ai' || trimmedEmail === 'analyst@bank.com') &&
      (pass === 'Demo@1234' || pass === 'demo' || pass === 'password')
    ) {
      const authUser: User = {
        email: trimmedEmail,
        name: 'Alex Vance',
        role: 'Lead Fraud Analyst (L2)',
      };
      setUser(authUser);
      localStorage.setItem('fraudsight_auth_user', JSON.stringify(authUser));
      return true;
    }
    // Also allow any realistic testing if demo account used
    if (trimmedEmail.includes('@') && pass.length >= 4) {
      const authUser: User = {
        email: trimmedEmail,
        name: trimmedEmail.split('@')[0].replace('.', ' ').replace(/^./, (s) => s.toUpperCase()),
        role: 'Fraud Investigator (L1)',
      };
      setUser(authUser);
      localStorage.setItem('fraudsight_auth_user', JSON.stringify(authUser));
      return true;
    }
    return false;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('fraudsight_auth_user');
  };

  useEffect(() => {
    if (user) {
      localStorage.setItem('fraudsight_auth_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('fraudsight_auth_user');
    }
  }, [user]);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
