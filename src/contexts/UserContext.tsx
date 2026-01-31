import { createContext } from 'react';

interface User {
  id: number;
  username: string;
  role: string;
  email: string;
}

interface UserContextType {
  user: User | null;
  setUser: (user: User | null) => void;
}

export const UserContext = createContext<UserContextType | undefined>(undefined);
export type { User, UserContextType };