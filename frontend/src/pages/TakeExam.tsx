import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Webcam from 'react-webcam';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { examAPI, sessionAPI, submissionAPI } from '@/lib/api';
import { getSocket, connectSocket } from '@/lib/socket';
import { useAuthStore } from '@/store/authStore';
import { Exam, Question, QuestionType } from '@/types';
import { getTimeRemaining, captureFrame } from '@/lib/utils';
import toast from 'react-hot-toast';
import { AlertTriangle, Camera, Monitor, Clock } from 'lucide-react';

export function TakeExam() {
  const { examId } = useParams<{ examId: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);

  const [exam, setExam] = useState<Exam | null>(null);
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState('');
  const [examStarted, setExamStarted] = useState(false);
  const [permissionsGranted, setPermissionsGranted] = useState(false);
  const [warningCount, setWarningCount] = useState(0);
  const [lastWarning, setLastWarning] = useState<string | null>(null);
  const [goodBehaviorStreak, setGoodBehaviorStreak] = useState(0);
  const [showPositiveFeedback, setShowPositiveFeedback] = useState(false);

  console.log('TakeExam component state:', {
    examId,
    loading,
    examStarted,
    permissionsGranted,
    hasExam: !!exam,
    hasSession: !!session,
    questionCount: exam?.questions?.length
  });

  const webcamRef = useRef<Webcam>(null);
  const monitoringInterval = useRef<NodeJS.Timeout | null>(null);
  const timerInterval = useRef<NodeJS.Timeout | null>(null);
  const socket = useRef(getSocket());

  // Secure browser mode: prevent tab switching, copy/paste, etc.
  useEffect(() => {
    if (!examStarted) return;

    const preventCopy = (e: ClipboardEvent) => {
      e.preventDefault();
      toast.error('Copying is disabled during the exam');
    };

    const preventPaste = (e: ClipboardEvent) => {
      e.preventDefault();
      toast.error('Pasting is disabled during the exam');
    };

    const preventContextMenu = (e: MouseEvent) => {
      e.preventDefault();
    };

    const preventKeyboardShortcuts = (e: KeyboardEvent) => {
      // Prevent F12, Ctrl+Shift+I, Ctrl+Shift+C, Ctrl+Shift+J (dev tools)
      if (
        e.key === 'F12' ||
        (e.ctrlKey && e.shiftKey && ['I', 'C', 'J'].includes(e.key)) ||
        (e.ctrlKey && ['u', 'U'].includes(e.key)) || // View source
        (e.metaKey && e.altKey && ['I', 'C', 'J'].includes(e.key)) // Mac
      ) {
        e.preventDefault();
        toast.error('Developer tools are disabled during the exam');
      }

      // Prevent print screen
      if (e.key === 'PrintScreen') {
        e.preventDefault();
        toast.error('Screenshots are disabled during the exam');
      }
    };

    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Tab switched or window minimized
        socket.current.emit('tab_switch_detected', {
          session_id: session?.id,
        });
        toast.error('Warning: Tab switch detected!');
      }
    };

    const handleBlur = () => {
      // Window lost focus
      socket.current.emit('tab_switch_detected', {
        session_id: session?.id,
      });
    };

    // Add event listeners
    document.addEventListener('copy', preventCopy);
    document.addEventListener('paste', preventPaste);
    document.addEventListener('contextmenu', preventContextMenu);
    document.addEventListener('keydown', preventKeyboardShortcuts);
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleBlur);

    // Try to enter fullscreen
    document.documentElement.requestFullscreen?.().catch(() => {
      console.log('Fullscreen not supported or denied');
    });

    return () => {
      document.removeEventListener('copy', preventCopy);
      document.removeEventListener('paste', preventPaste);
      document.removeEventListener('contextmenu', preventContextMenu);
      document.removeEventListener('keydown', preventKeyboardShortcuts);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleBlur);

      if (document.fullscreenElement) {
        document.exitFullscreen?.();
      }
    };
  }, [examStarted, session]);

  // Load exam and start session
  useEffect(() => {
    const loadExam = async () => {
      try {
        console.log('Loading exam with ID:', examId);
        const { data } = await examAPI.get(Number(examId));
        console.log('Exam data received:', data);
        setExam(data);

        // Check if exam is active
        const now = new Date();
        const startTime = new Date(data.start_time);
        const endTime = new Date(data.end_time);

        if (now < startTime) {
          console.error('Exam has not started yet');
          toast.error('Exam has not started yet');
          navigate('/dashboard');
          return;
        }

        if (now > endTime) {
          console.error('Exam has ended');
          toast.error('Exam has ended');
          navigate('/dashboard');
          return;
        }

        // Start session
        console.log('Starting exam session...');
        const sessionRes = await sessionAPI.start(Number(examId));
        console.log('Session started:', sessionRes.data);
        setSession(sessionRes.data);

        console.log('Exam loaded successfully with', data.questions?.length, 'questions');
        setLoading(false);
      } catch (error: any) {
        console.error('Error loading exam:', error);
        toast.error(error.response?.data?.detail || 'Failed to load exam');
        navigate('/dashboard');
      }
    };

    loadExam();
  }, [examId, navigate]);

  // Request permissions
  const requestPermissions = async () => {
    try {
      // Request camera permission
      await navigator.mediaDevices.getUserMedia({ video: true, audio: false });

      setPermissionsGranted(true);
      toast.success('Permissions granted. You can now start the exam.');
    } catch (error) {
      toast.error('Camera permission is required to take this exam');
    }
  };

  // Start exam
  const startExam = () => {
    if (!permissionsGranted) {
      toast.error('Please grant camera permissions first');
      return;
    }

    // Validate exam data
    if (!exam || !exam.questions || exam.questions.length === 0) {
      toast.error('Exam data is invalid or has no questions');
      console.error('Exam data:', exam);
      return;
    }

    if (!session) {
      toast.error('Exam session not initialized');
      console.error('Session data:', session);
      return;
    }

    console.log('Starting exam with data:', { exam, session, user });

    setExamStarted(true);

    // Connect to socket
    try {
      connectSocket();
      console.log('Socket connected');

      socket.current.emit('join_exam_session', {
        session_id: session.id,
        student_id: user?.id,
        exam_id: exam?.id,
      });

      // Listen for auto-submission
      socket.current.on('exam_auto_submitted', (data: any) => {
        toast.error(`Exam auto-submitted: ${data.reason}`);
        handleSubmit(true);
      });

      // Listen for cheating warnings
      socket.current.on('cheating_warning', (data: any) => {
        console.log('Received cheating warning:', data);
        setWarningCount(prev => prev + 1);
        setLastWarning(data.description || 'Suspicious activity detected');
        toast.error(`⚠️ WARNING: ${data.description}`, { duration: 5000 });
      });

      // Listen for proctoring alerts (less severe)
      socket.current.on('proctoring_alert', (data: any) => {
        console.log('Received proctoring alert:', data);
        toast((t) => (
          <div className="flex items-center gap-2">
            <AlertTriangle className="text-yellow-600" size={20} />
            <span>{data.description}</span>
          </div>
        ), { duration: 3000 });
      });

      // Listen for positive feedback
      socket.current.on('positive_feedback', (data: any) => {
        console.log('Received positive feedback:', data);
        setGoodBehaviorStreak(data.good_behavior_streak);
        setShowPositiveFeedback(true);

        // Clear warning banner when good behavior is shown
        setLastWarning(null);

        // Hide positive feedback after 4 seconds
        setTimeout(() => setShowPositiveFeedback(false), 4000);

        toast.success(data.message, {
          duration: 4000,
          icon: '✅',
          style: {
            background: '#10b981',
            color: 'white',
            fontWeight: '600',
          },
        });
      });

      // Start monitoring
      startMonitoring();

      // Start timer
      startTimer();

      toast.success('Exam started. Good luck!');
    } catch (error) {
      console.error('Error starting exam:', error);
      toast.error('Failed to start exam. Please try again.');
      setExamStarted(false);
    }
  };

  // Start AI monitoring
  const startMonitoring = () => {
    let frameCount = 0;
    monitoringInterval.current = setInterval(() => {
      if (webcamRef.current?.video) {
        const frame = captureFrame(webcamRef.current.video);

        if (frame) {
          frameCount++;
          if (frameCount % 10 === 0) {
            console.log(`📸 Real-time monitoring: ${frameCount} frames analyzed`);
          }
          socket.current.emit('analyze_frame', {
            session_id: session.id,
            webcam_frame: frame,
          });
        }
      }
    }, 500); // Analyze every 0.5 seconds for real-time detection
  };

  // Start timer
  const startTimer = () => {
    // Calculate end time from NOW (client time), not from session.start_time
    // This avoids timezone issues between backend and frontend
    const now = new Date();
    const endTime = new Date(now.getTime() + exam!.duration_minutes * 60 * 1000);

    console.log('Timer started at:', now.toISOString());
    console.log('Timer will end at:', endTime.toISOString());
    console.log('Duration:', exam!.duration_minutes, 'minutes');

    const updateTimer = () => {
      const remaining = getTimeRemaining(endTime);
      setTimeRemaining(remaining);

      if (remaining === '00:00:00') {
        console.log('Time expired! Auto-submitting exam');
        handleSubmit(true);
      }
    };

    updateTimer();
    timerInterval.current = setInterval(updateTimer, 1000);
  };

  // Cleanup
  useEffect(() => {
    return () => {
      if (monitoringInterval.current) {
        clearInterval(monitoringInterval.current);
      }
      if (timerInterval.current) {
        clearInterval(timerInterval.current);
      }
    };
  }, []);

  // Handle answer change
  const handleAnswerChange = (questionId: number, value: string) => {
    setAnswers({ ...answers, [questionId]: value });
  };

  // Submit exam
  const handleSubmit = async (autoSubmit = false) => {
    console.log('handleSubmit called, autoSubmit:', autoSubmit);

    if (!autoSubmit && !confirm('Are you sure you want to submit the exam?')) {
      console.log('User cancelled submission');
      return;
    }

    try {
      console.log('Submitting exam...');
      // Stop monitoring
      if (monitoringInterval.current) {
        clearInterval(monitoringInterval.current);
      }
      if (timerInterval.current) {
        clearInterval(timerInterval.current);
      }

      // Prepare answers
      const submissionAnswers = exam!.questions!.map((q) => ({
        question_id: q.id,
        answer_text: answers[q.id] || '',
      }));

      console.log('Submitting answers:', submissionAnswers);
      // Submit
      await submissionAPI.submit(session.id, submissionAnswers);

      console.log('Exam submitted successfully, navigating to dashboard');
      toast.success('Exam submitted successfully!');
      navigate('/dashboard');
    } catch (error: any) {
      console.error('Error submitting exam:', error);
      toast.error(error.response?.data?.detail || 'Failed to submit exam');
    }
  };

  if (loading) {
    console.log('Rendering: Loading screen');
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading exam...</p>
        </div>
      </div>
    );
  }

  if (!examStarted) {
    console.log('Rendering: Pre-exam screen (not started yet)');
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50 dark:bg-gray-900">
        <Card className="max-w-2xl w-full">
          <CardContent className="p-8">
            <h1 className="text-3xl font-bold mb-4">{exam?.title}</h1>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              {exam?.description}
            </p>

            <div className="space-y-4 mb-8">
              <div className="flex items-center gap-2">
                <Clock className="text-primary-600" size={20} />
                <span>Duration: {exam?.duration_minutes} minutes</span>
              </div>
              <div className="flex items-center gap-2">
                <AlertTriangle className="text-yellow-600" size={20} />
                <span>Questions: {exam?.questions?.length}</span>
              </div>
            </div>

            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-6">
              <h3 className="font-semibold mb-2 flex items-center gap-2">
                <AlertTriangle className="text-yellow-600" size={20} />
                Important Instructions
              </h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 dark:text-gray-300">
                <li>Camera access is required for proctoring</li>
                <li>Do not switch tabs or windows during the exam</li>
                <li>Copying and pasting are disabled</li>
                <li>The exam will be in fullscreen mode</li>
                <li>AI will monitor for suspicious behavior</li>
                <li>Excessive cheating attempts will auto-submit the exam</li>
              </ul>
            </div>

            {!permissionsGranted ? (
              <Button onClick={requestPermissions} className="w-full" size="lg">
                <Camera className="mr-2" size={20} />
                Grant Camera Permission
              </Button>
            ) : (
              <Button onClick={startExam} className="w-full" size="lg">
                Start Exam
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  const currentQuestion = exam?.questions?.[currentQuestionIndex];

  console.log('Rendering exam interface:', {
    examStarted,
    hasExam: !!exam,
    hasQuestions: !!exam?.questions,
    questionCount: exam?.questions?.length,
    currentQuestionIndex,
    currentQuestion: !!currentQuestion
  });

  if (!exam || !exam.questions || exam.questions.length === 0) {
    console.error('Cannot render exam: missing data');
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 dark:text-red-400">Error: Exam data is missing or invalid</p>
          <Button onClick={() => navigate('/dashboard')} className="mt-4">
            Return to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 exam-mode no-copy">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold">{exam?.title}</h1>

          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
              <Camera size={20} className="text-green-600 animate-pulse" />
              <span className="text-sm">
                <span className="font-semibold text-green-600">●</span> Real-Time Monitoring (0.5s)
              </span>
            </div>

            {showPositiveFeedback && (
              <div className="flex items-center gap-2 px-3 py-1 bg-green-100 dark:bg-green-900/30 border border-green-300 dark:border-green-700 rounded-lg animate-pulse">
                <span className="text-2xl">✅</span>
                <span className="text-sm font-semibold text-green-700 dark:text-green-300">
                  Great Job! Behaving Well
                </span>
              </div>
            )}

            {warningCount > 0 && (
              <div className="flex items-center gap-2 px-3 py-1 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg">
                <AlertTriangle size={20} className="text-red-600 dark:text-red-400" />
                <span className="text-sm font-semibold text-red-700 dark:text-red-300">
                  {warningCount} Warning{warningCount > 1 ? 's' : ''}
                </span>
              </div>
            )}

            <div className="flex items-center gap-2">
              <Clock size={20} className="text-primary-600" />
              <span className="text-lg font-mono font-bold">{timeRemaining}</span>
            </div>

            <Button onClick={() => handleSubmit(false)} variant="primary">
              Submit Exam
            </Button>
          </div>
        </div>
      </div>

      {/* Warning Banner */}
      {lastWarning && (
        <div className="bg-red-50 dark:bg-red-900/20 border-b-2 border-red-300 dark:border-red-700">
          <div className="max-w-7xl mx-auto px-4 py-3">
            <div className="flex items-center gap-3">
              <AlertTriangle size={24} className="text-red-600 dark:text-red-400 animate-pulse" />
              <div>
                <p className="font-semibold text-red-800 dark:text-red-200">
                  Suspicious Activity Detected
                </p>
                <p className="text-sm text-red-700 dark:text-red-300">
                  {lastWarning}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Positive Feedback Banner */}
      {showPositiveFeedback && !lastWarning && (
        <div className="bg-green-50 dark:bg-green-900/20 border-b-2 border-green-300 dark:border-green-700">
          <div className="max-w-7xl mx-auto px-4 py-3">
            <div className="flex items-center gap-3">
              <span className="text-3xl">✅</span>
              <div>
                <p className="font-semibold text-green-800 dark:text-green-200">
                  Excellent Behavior!
                </p>
                <p className="text-sm text-green-700 dark:text-green-300">
                  You're maintaining great focus. Keep up the good work!
                  {goodBehaviorStreak > 0 && ` (${goodBehaviorStreak} consecutive good checks)`}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Webcam Preview */}
          <div className="lg:col-span-1">
            <Card className="sticky top-24">
              <CardContent className="p-4">
                <h3 className="font-semibold mb-2 flex items-center gap-2">
                  <Camera size={16} />
                  Camera Feed
                </h3>
                <Webcam
                  ref={webcamRef}
                  audio={false}
                  screenshotFormat="image/jpeg"
                  className="w-full rounded-lg"
                />
                <p className="text-xs text-gray-500 mt-2">
                  Your camera is being monitored
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Questions */}
          <div className="lg:col-span-3">
            <Card>
              <CardContent className="p-6">
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold">
                      Question {currentQuestionIndex + 1} of {exam?.questions?.length}
                    </h2>
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {currentQuestion?.points} points
                    </span>
                  </div>

                  <p className="text-lg mb-6">{currentQuestion?.question_text}</p>

                  {/* Answer input based on question type */}
                  {currentQuestion?.question_type === QuestionType.MCQ && (
                    <div className="space-y-3">
                      {Object.entries(currentQuestion.options || {}).map(([key, value]) => (
                        <label
                          key={key}
                          className="flex items-center gap-3 p-4 border border-gray-200 dark:border-gray-700 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                        >
                          <input
                            type="radio"
                            name={`question-${currentQuestion.id}`}
                            value={key}
                            checked={answers[currentQuestion.id] === key}
                            onChange={(e) =>
                              handleAnswerChange(currentQuestion.id, e.target.value)
                            }
                            className="w-4 h-4"
                          />
                          <span>{key}. {value}</span>
                        </label>
                      ))}
                    </div>
                  )}

                  {currentQuestion?.question_type === QuestionType.SHORT_ANSWER && (
                    <input
                      type="text"
                      value={answers[currentQuestion.id] || ''}
                      onChange={(e) =>
                        handleAnswerChange(currentQuestion.id, e.target.value)
                      }
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900"
                      placeholder="Type your answer..."
                    />
                  )}

                  {(currentQuestion?.question_type === QuestionType.LONG_ANSWER ||
                    currentQuestion?.question_type === QuestionType.CODING) && (
                    <textarea
                      value={answers[currentQuestion.id] || ''}
                      onChange={(e) =>
                        handleAnswerChange(currentQuestion.id, e.target.value)
                      }
                      rows={10}
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 font-mono"
                      placeholder={
                        currentQuestion.question_type === QuestionType.CODING
                          ? 'Write your code here...'
                          : 'Type your answer...'
                      }
                    />
                  )}
                </div>

                {/* Navigation */}
                <div className="flex justify-between mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
                  <Button
                    variant="outline"
                    onClick={() =>
                      setCurrentQuestionIndex(Math.max(0, currentQuestionIndex - 1))
                    }
                    disabled={currentQuestionIndex === 0}
                  >
                    Previous
                  </Button>

                  <div className="flex gap-2">
                    {exam?.questions?.map((_, index) => (
                      <button
                        key={index}
                        onClick={() => setCurrentQuestionIndex(index)}
                        className={`w-10 h-10 rounded-lg font-medium transition-colors ${
                          index === currentQuestionIndex
                            ? 'bg-primary-600 text-white'
                            : answers[exam.questions![index].id]
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100'
                            : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100'
                        }`}
                      >
                        {index + 1}
                      </button>
                    ))}
                  </div>

                  <Button
                    variant="outline"
                    onClick={() =>
                      setCurrentQuestionIndex(
                        Math.min(exam!.questions!.length - 1, currentQuestionIndex + 1)
                      )
                    }
                    disabled={currentQuestionIndex === exam!.questions!.length - 1}
                  >
                    Next
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
