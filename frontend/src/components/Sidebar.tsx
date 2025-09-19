import React from 'react';
import { MessageCircle, FileText, Activity, Image, LogIn, LogOut } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isAuthenticated: boolean;
  onLoginClick: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, isAuthenticated, onLoginClick }) => {
  const { user, logout } = useAuth();

  const menuItems = [
    { id: 'chat', label: 'AI 채팅', icon: MessageCircle, requiresAuth: false },
    { id: 'policies', label: '약관 관리', icon: FileText, requiresAuth: true },
    { id: 'workflow', label: '워크플로우', icon: Activity, requiresAuth: true },
    { id: 'image', label: '이미지 분석', icon: Image, requiresAuth: true },
  ];

  return (
    <div className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
      {/* 로고 */}
      <div className="p-6 border-b border-gray-700">
        <h2 className="text-xl font-bold text-white">ISPL AI</h2>
        <p className="text-sm text-gray-400">보험약관 AI</p>
      </div>

      {/* 메뉴 */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isDisabled = item.requiresAuth && !isAuthenticated;
            
            return (
              <li key={item.id}>
                <button
                  onClick={() => {
                    if (isDisabled) {
                      onLoginClick();
                    } else {
                      setActiveTab(item.id);
                    }
                  }}
                  className={`w-full flex items-center px-4 py-3 text-left rounded-lg transition-colors ${
                    activeTab === item.id
                      ? 'bg-blue-600 text-white'
                      : isDisabled
                      ? 'text-gray-500 cursor-not-allowed'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                  disabled={isDisabled}
                >
                  <Icon className="w-5 h-5 mr-3" />
                  {item.label}
                  {isDisabled && <span className="ml-auto text-xs">(로그인 필요)</span>}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* 사용자 정보 및 로그인/로그아웃 */}
      <div className="p-4 border-t border-gray-700">
        {isAuthenticated ? (
          <>
            <div className="flex items-center mb-4">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                {user?.email?.charAt(0).toUpperCase()}
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-white">{user?.email}</p>
                <p className="text-xs text-gray-400">{user?.role}</p>
              </div>
            </div>
            
            <button
              onClick={logout}
              className="w-full flex items-center px-4 py-2 text-left text-gray-300 hover:bg-gray-700 hover:text-white rounded-lg transition-colors"
            >
              <LogOut className="w-5 h-5 mr-3" />
              로그아웃
            </button>
          </>
        ) : (
          <button
            onClick={onLoginClick}
            className="w-full flex items-center px-4 py-2 text-left text-gray-300 hover:bg-gray-700 hover:text-white rounded-lg transition-colors"
          >
            <LogIn className="w-5 h-5 mr-3" />
            로그인
          </button>
        )}
      </div>
    </div>
  );
};

export default Sidebar;
