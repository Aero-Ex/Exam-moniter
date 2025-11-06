import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { adminAPI, sessionAPI } from '@/lib/api';
import { getSocket, connectSocket } from '@/lib/socket';
import { ExamSession, MonitoringEvent } from '@/types';
import { formatDateTime, getAlertTypeLabel, getRiskLevel } from '@/lib/utils';
import toast from 'react-hot-toast';
import { AlertTriangle, Camera, User, Clock, ArrowLeft } from 'lucide-react';

export function AdminPanel() {
  const { examId } = useParams<{ examId: string }>();
  const navigate = useNavigate();

  const [sessions, setSessions] = useState<ExamSession[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const socket = getSocket();

  useEffect(() => {
    loadSessions();
    connectSocket();

    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }

    // Join proctor room
    socket.emit('join_proctor_room', { exam_id: examId });

    // Listen for alerts
    socket.on('cheating_alert', (alert: any) => {
      console.log('🚨 Real-time alert received:', alert);
      setAlerts((prev) => [alert, ...prev]);

      // Play alert sound for high severity
      if (alert.severity >= 3) {
        try {
          const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBi6Fzf');
          audio.volume = 0.3;
          audio.play();
        } catch (e) {
          console.log('Could not play alert sound');
        }
      }

      // Show desktop notification
      if ('Notification' in window && Notification.permission === 'granted') {
        const notification = new Notification('🚨 Exam Proctoring Alert', {
          body: `Student ${alert.student_id}: ${alert.description}`,
          icon: '/favicon.ico',
          tag: `alert-${alert.session_id}-${Date.now()}`,
          requireInteraction: alert.severity >= 4, // Keep visible for high severity
        });

        notification.onclick = () => {
          window.focus();
          notification.close();
        };
      }

      toast.error(
        `🚨 ${alert.severity >= 4 ? 'HIGH RISK' : 'Alert'} - Student ${alert.student_id}: ${alert.description}`,
        {
          duration: 7000,
          style: {
            background: alert.severity >= 4 ? '#dc2626' : '#ef4444',
            color: 'white',
            fontWeight: 'bold',
          },
        }
      );
    });

    return () => {
      socket.off('cheating_alert');
    };
  }, [examId]);

  const loadSessions = async () => {
    try {
      if (examId) {
        const { data } = await adminAPI.getExamSessions(Number(examId));
        setSessions(data);
      } else {
        const { data } = await adminAPI.getLiveSessions();
        setSessions(data.active_sessions);
      }
    } catch (error) {
      toast.error('Failed to load sessions');
    } finally {
      setLoading(false);
    }
  };

  const viewBehaviorReport = async (sessionId: number) => {
    try {
      const { data } = await sessionAPI.getBehaviorReport(sessionId);

      // Display report in modal or new page
      alert(
        `Behavior Report\n\nTotal Alerts: ${data.total_alerts}\nRisk Score: ${data.risk_score}/10\n\nSummary: ${data.summary}`
      );
    } catch (error) {
      toast.error('Failed to load behavior report');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading sessions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard')}>
                <ArrowLeft size={20} />
              </Button>
              <div>
                <h1 className="text-2xl font-bold">Live Proctoring Dashboard</h1>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Monitor exam sessions in real-time
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {alerts.length > 0 && (
                <div className="flex items-center gap-2 px-3 py-1 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg">
                  <AlertTriangle size={18} className="text-red-600 dark:text-red-400 animate-pulse" />
                  <span className="text-sm font-semibold text-red-700 dark:text-red-300">
                    {alerts.length} Alert{alerts.length > 1 ? 's' : ''}
                  </span>
                </div>
              )}
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">Live</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Active Sessions */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Active Sessions ({sessions.length})</CardTitle>
              </CardHeader>
              <CardContent>
                {sessions.length === 0 ? (
                  <div className="text-center py-12">
                    <Camera size={48} className="mx-auto text-gray-400 mb-4" />
                    <p className="text-gray-600 dark:text-gray-400">
                      No active sessions
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {sessions.map((session) => {
                      const riskLevel = getRiskLevel(session.cheating_score);

                      return (
                        <div
                          key={session.id}
                          className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                        >
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center">
                                <User size={20} className="text-primary-600" />
                              </div>
                              <div>
                                <p className="font-medium">Student ID: {session.student_id}</p>
                                <p className="text-sm text-gray-600 dark:text-gray-400">
                                  Session #{session.id}
                                </p>
                              </div>
                            </div>

                            <div className="text-right">
                              <p className={`font-semibold ${riskLevel.color}`}>
                                {riskLevel.label}
                              </p>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                Score: {session.cheating_score}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center justify-between text-sm">
                            <div className="flex items-center gap-4">
                              <span className="flex items-center gap-1">
                                <AlertTriangle size={14} className="text-yellow-600" />
                                {session.total_alerts} alerts
                              </span>
                              <span className="flex items-center gap-1">
                                <Clock size={14} />
                                {formatDateTime(session.start_time)}
                              </span>
                            </div>

                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => viewBehaviorReport(session.id)}
                              >
                                View Report
                              </Button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Live Alerts */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Live Alerts</CardTitle>
              </CardHeader>
              <CardContent>
                {alerts.length === 0 ? (
                  <div className="text-center py-8">
                    <AlertTriangle size={32} className="mx-auto text-gray-400 mb-2" />
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      No alerts yet
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-[600px] overflow-y-auto">
                    {alerts.map((alert, index) => {
                      const severityColors = {
                        1: 'border-yellow-400 bg-yellow-50 dark:bg-yellow-900/20',
                        2: 'border-orange-500 bg-orange-50 dark:bg-orange-900/20',
                        3: 'border-red-500 bg-red-50 dark:bg-red-900/20',
                        4: 'border-red-600 bg-red-100 dark:bg-red-900/30',
                        5: 'border-red-700 bg-red-200 dark:bg-red-900/40'
                      };
                      const severityColor = severityColors[alert.severity as keyof typeof severityColors] || severityColors[3];

                      return (
                        <div
                          key={index}
                          className={`border-l-4 ${severityColor} p-3 rounded animate-slideIn`}
                        >
                          <div className="flex items-start justify-between mb-1">
                            <div className="flex items-center gap-2">
                              <User size={14} />
                              <p className="font-medium text-sm">
                                Student {alert.student_id}
                              </p>
                              {alert.severity >= 4 && (
                                <span className="px-2 py-0.5 bg-red-600 text-white text-xs rounded-full font-semibold">
                                  HIGH RISK
                                </span>
                              )}
                            </div>
                            <span className="text-xs text-gray-500">
                              {new Date(alert.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                          <p className="text-sm font-medium text-red-700 dark:text-red-400">
                            {getAlertTypeLabel(alert.event_type)}
                          </p>
                          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                            {alert.description}
                          </p>
                          <div className="flex items-center gap-4 mt-2">
                            {alert.confidence !== undefined && (
                              <span className="text-xs text-gray-500">
                                Confidence: {(alert.confidence * 100).toFixed(0)}%
                              </span>
                            )}
                            <span className="text-xs text-gray-500">
                              Severity: {alert.severity}/5
                            </span>
                          </div>
                          {alert.evidence_url && (
                            <button
                              className="text-xs text-primary-600 hover:underline mt-2 font-medium"
                              onClick={() => window.open(alert.evidence_url, '_blank')}
                            >
                              📷 View Evidence
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
