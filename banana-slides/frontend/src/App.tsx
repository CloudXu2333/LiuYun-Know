import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Home } from './pages/Home';
import { History } from './pages/History';
import { OutlineEditor } from './pages/OutlineEditor';
import { DetailEditor } from './pages/DetailEditor';
import { SlidePreview } from './pages/SlidePreview';
import { SettingsPage } from './pages/Settings';
import { useProjectStore } from './store/useProjectStore';
import { useToast } from './components/shared';

// 路由变化通知组件
function RouteChangeNotifier() {
  const location = useLocation();

  useEffect(() => {
    // 向父窗口发送当前路径
    window.parent.postMessage({
      type: 'ROUTE_CHANGE',
      path: location.pathname
    }, '*');
  }, [location]);

  return null;
}

function App() {
  const { currentProject, syncProject, error, setError } = useProjectStore();
  const { show, ToastContainer } = useToast();

  // 恢复项目状态
  useEffect(() => {
    const savedProjectId = localStorage.getItem('currentProjectId');
    if (savedProjectId && !currentProject) {
      syncProject();
    }
  }, [currentProject, syncProject]);

  // 解析并保存用户ID
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const uid = params.get('uid');

    if (uid) {
      const storedUid = localStorage.getItem('banana_user_id');

      // 如果检测到新用户登录，清除本地缓存的所有项目状态
      if (storedUid && storedUid !== uid) {
        console.log('[App] 用户切换 detected:', storedUid, '->', uid);
        localStorage.removeItem('currentProjectId');
        useProjectStore.getState().setCurrentProject(null);
        // 如果有其他需要清除的缓存也可以在这里处理
      }

      localStorage.setItem('banana_user_id', uid);
      // 可选：清除URL中的uid参数，保持URL整洁
      // window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);

  // 显示全局错误
  useEffect(() => {
    if (error) {
      show({ message: error, type: 'error' });
      setError(null);
    }
  }, [error, setError, show]);

  return (
    <BrowserRouter>
      <RouteChangeNotifier />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/history" element={<History />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/project/:projectId/outline" element={<OutlineEditor />} />
        <Route path="/project/:projectId/detail" element={<DetailEditor />} />
        <Route path="/project/:projectId/preview" element={<SlidePreview />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <ToastContainer />
    </BrowserRouter>
  );
}

export default App;
