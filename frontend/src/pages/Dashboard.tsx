import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useAuthStore } from '@/store/authStore';
import { useThemeStore } from '@/store/themeStore';
import { examAPI } from '@/lib/api';
import { Exam, UserRole } from '@/types';
import { formatDateTime, formatDuration } from '@/lib/utils';
import toast from 'react-hot-toast';
import { Moon, Sun, Calendar, Clock, FileText, LogOut, Plus, Users } from 'lucide-react';

export function Dashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();

  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadExams();
  }, []);

  const loadExams = async () => {
    try {
      const { data } = await examAPI.list();
      setExams(data);
    } catch (error) {
      toast.error('Failed to load exams');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    toast.success('Logged out successfully');
  };

  const getExamStatus = (exam: Exam) => {
    const now = new Date();
    const startTime = new Date(exam.start_time);
    const endTime = new Date(exam.end_time);

    if (now < startTime) {
      return { status: 'upcoming', color: 'text-blue-600', label: 'Upcoming' };
    } else if (now > endTime) {
      return { status: 'ended', color: 'text-gray-600', label: 'Ended' };
    } else {
      return { status: 'active', color: 'text-green-600', label: 'Active' };
    }
  };

  const isTeacherOrAdmin = user?.role === UserRole.TEACHER || user?.role === UserRole.ADMIN;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Exam Platform</h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Welcome back, {user?.full_name}
              </p>
            </div>

            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleTheme}
                className="rounded-full p-2"
              >
                {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
              </Button>

              {isTeacherOrAdmin && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate('/admin')}
                  >
                    <Users size={16} className="mr-2" />
                    Admin Panel
                  </Button>

                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => navigate('/create-exam')}
                  >
                    <Plus size={16} className="mr-2" />
                    Create Exam
                  </Button>
                </>
              )}

              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut size={16} className="mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Exams</p>
                  <p className="text-3xl font-bold">{exams.length}</p>
                </div>
                <FileText size={40} className="text-primary-600 opacity-20" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Active Exams</p>
                  <p className="text-3xl font-bold">
                    {exams.filter((e) => getExamStatus(e).status === 'active').length}
                  </p>
                </div>
                <Calendar size={40} className="text-green-600 opacity-20" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Upcoming Exams</p>
                  <p className="text-3xl font-bold">
                    {exams.filter((e) => getExamStatus(e).status === 'upcoming').length}
                  </p>
                </div>
                <Clock size={40} className="text-blue-600 opacity-20" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Exams List */}
        <div>
          <h2 className="text-2xl font-bold mb-6">
            {isTeacherOrAdmin ? 'All Exams' : 'My Exams'}
          </h2>

          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">Loading exams...</p>
            </div>
          ) : exams.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <FileText size={48} className="mx-auto text-gray-400 mb-4" />
                <p className="text-gray-600 dark:text-gray-400">No exams available</p>
                {isTeacherOrAdmin && (
                  <Button
                    variant="primary"
                    className="mt-4"
                    onClick={() => navigate('/create-exam')}
                  >
                    Create Your First Exam
                  </Button>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {exams.map((exam) => {
                const status = getExamStatus(exam);

                return (
                  <Card key={exam.id} className="hover:shadow-md transition-shadow">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-xl">{exam.title}</CardTitle>
                          <CardDescription className="mt-1">
                            {exam.description}
                          </CardDescription>
                        </div>
                        <span className={`text-sm font-medium ${status.color}`}>
                          {status.label}
                        </span>
                      </div>
                    </CardHeader>

                    <CardContent>
                      <div className="space-y-3 mb-4">
                        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                          <Calendar size={16} />
                          <span>Start: {formatDateTime(exam.start_time)}</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                          <Clock size={16} />
                          <span>Duration: {formatDuration(exam.duration_minutes)}</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                          <FileText size={16} />
                          <span>Questions: {exam.total_questions || 0}</span>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        {status.status === 'active' && !isTeacherOrAdmin && (
                          <Button
                            variant="primary"
                            className="flex-1"
                            onClick={() => navigate(`/exam/${exam.id}`)}
                          >
                            Take Exam
                          </Button>
                        )}

                        <Button
                          variant="outline"
                          className="flex-1"
                          onClick={() => navigate(`/exam/${exam.id}/details`)}
                        >
                          View Details
                        </Button>

                        {isTeacherOrAdmin && (
                          <Button
                            variant="secondary"
                            onClick={() => navigate(`/admin/exam/${exam.id}/monitor`)}
                          >
                            Monitor
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
