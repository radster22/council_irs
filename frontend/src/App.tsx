import { Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { DashboardPage } from './routes/DashboardPage';
import { LoginPage } from './routes/LoginPage';
import { ReportEditorPage } from './routes/ReportEditorPage';
import { ReviewPage } from './routes/ReviewPage';
import { useAuth } from './hooks/useAuth';
import { ReviewDetailPage } from './routes/ReviewDetailPage';
import { UserPage } from './routes/UserPage';
import { AccessDeniedPage } from './routes/AccessDeniedPage';
import { InitiativeAdminPage } from './routes/InitiativeAdminPage';
import { RolloverPage } from './routes/RolloverPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return <div className="p-8 text-sm text-slate-500">Checking your session…</div>;

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function HomeRoute() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={user.role === 'EXTERNAL_SUBMITTER' ? '/submit' : '/review'} replace />;
}

function RoleRoute({ children, roles, portal }: { children: React.ReactNode; roles: string[]; portal: 'submitter' | 'council' }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-sm text-slate-500">Checking your access…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (!roles.includes(user.role)) return <AccessDeniedPage />;
  return <Layout portal={portal}>{children}</Layout>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<ProtectedRoute><HomeRoute /></ProtectedRoute>} />
      <Route path="/submit" element={<RoleRoute roles={['EXTERNAL_SUBMITTER']} portal="submitter"><DashboardPage /></RoleRoute>} />
      <Route
        path="/reports/:reportId"
        element={
          <RoleRoute roles={['EXTERNAL_SUBMITTER']} portal="submitter"><ReportEditorPage /></RoleRoute>
        }
      />
      <Route
        path="/review"
        element={
          <RoleRoute roles={['COUNCIL_ADMIN', 'COUNCIL_REVIEWER', 'VIEW_ONLY']} portal="council"><ReviewPage /></RoleRoute>
        }
      />
      <Route path="/review/:submissionId" element={<RoleRoute roles={['COUNCIL_ADMIN', 'COUNCIL_REVIEWER', 'VIEW_ONLY']} portal="council"><ReviewDetailPage /></RoleRoute>} />
      <Route path="/review/:submissionId/edit" element={<RoleRoute roles={['COUNCIL_ADMIN']} portal="council"><ReportEditorPage /></RoleRoute>} />
      <Route path="/user_page" element={<RoleRoute roles={['COUNCIL_ADMIN']} portal="council"><UserPage /></RoleRoute>} />
      <Route path="/admin/initiatives" element={<RoleRoute roles={['COUNCIL_ADMIN']} portal="council"><InitiativeAdminPage /></RoleRoute>} />
      <Route path="/admin/rollover" element={<RoleRoute roles={['COUNCIL_ADMIN']} portal="council"><RolloverPage /></RoleRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
