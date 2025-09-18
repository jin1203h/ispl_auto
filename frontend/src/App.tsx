import React, { useState } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import PolicyManagement from './components/PolicyManagement';
import WorkflowMonitor from './components/WorkflowMonitor';
import ImageAnalysis from './components/ImageAnalysis';
import Login from './components/Login';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import './App.css';

function AppContent() {
  const { isAuthenticated, loading } = useAuth();
  const [activeTab, setActiveTab] = useState('chat');
  const [showLogin, setShowLogin] = useState(false);

  // 로딩 중일 때 로딩 화면 표시
  if (loading) {
    return (
      <div className="flex h-screen bg-gray-900 text-white items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">로딩 중...</p>
        </div>
      </div>
    );
  }

  if (showLogin) {
    return <Login onClose={() => setShowLogin(false)} />;
  }

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        isAuthenticated={isAuthenticated}
        onLoginClick={() => setShowLogin(true)}
      />
      <main className="flex-1 flex flex-col">
        <header className="bg-gray-800 px-6 py-4 border-b border-gray-700">
          <h1 className="text-xl font-semibold">ISPL Insurance Policy AI</h1>
          <p className="text-sm text-gray-400">보험약관 기반 AI 시스템</p>
        </header>
        
        <div className="flex-1 overflow-hidden">
          <div className="h-full overflow-y-auto">
            {activeTab === 'chat' && <ChatInterface isAuthenticated={isAuthenticated} />}
            {activeTab === 'policies' && <PolicyManagement isAuthenticated={isAuthenticated} />}
            {activeTab === 'workflow' && <WorkflowMonitor isAuthenticated={isAuthenticated} />}
            {activeTab === 'image' && <ImageAnalysis isAuthenticated={isAuthenticated} />}
          </div>
        </div>
      </main>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  );
}

export default App;
