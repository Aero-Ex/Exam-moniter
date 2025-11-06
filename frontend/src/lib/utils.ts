import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export function formatDateTime(date: string | Date): string {
  return new Date(date).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;

  if (hours > 0) {
    return `${hours}h ${mins}m`;
  }
  return `${mins}m`;
}

export function getTimeRemaining(endTime: Date): string {
  const now = new Date();
  const diff = endTime.getTime() - now.getTime();

  if (diff <= 0) {
    return '00:00:00';
  }

  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((diff % (1000 * 60)) / 1000);

  return `${hours.toString().padStart(2, '0')}:${minutes
    .toString()
    .padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

export function captureFrame(videoElement: HTMLVideoElement): string {
  const canvas = document.createElement('canvas');
  canvas.width = videoElement.videoWidth;
  canvas.height = videoElement.videoHeight;

  const ctx = canvas.getContext('2d');
  if (!ctx) return '';

  ctx.drawImage(videoElement, 0, 0);

  // Convert to base64 (without data:image/jpeg;base64, prefix)
  return canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
}

export async function captureScreen(): Promise<string | null> {
  try {
    const stream = await navigator.mediaDevices.getDisplayMedia({
      video: { mediaSource: 'screen' } as any,
    });

    const video = document.createElement('video');
    video.srcObject = stream;
    video.play();

    // Wait for video to be ready
    await new Promise((resolve) => {
      video.onloadedmetadata = resolve;
    });

    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    ctx.drawImage(video, 0, 0);

    // Stop the stream
    stream.getTracks().forEach((track) => track.stop());

    return canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
  } catch (error) {
    console.error('Screen capture failed:', error);
    return null;
  }
}

export function getRiskLevel(score: number): { label: string; color: string } {
  if (score < 2) {
    return { label: 'Low Risk', color: 'text-green-600' };
  } else if (score < 5) {
    return { label: 'Moderate Risk', color: 'text-yellow-600' };
  } else if (score < 8) {
    return { label: 'High Risk', color: 'text-orange-600' };
  } else {
    return { label: 'Critical Risk', color: 'text-red-600' };
  }
}

export function getAlertTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    looking_away: 'Looking Away',
    multiple_people: 'Multiple People',
    phone_detected: 'Phone Detected',
    reading_from_material: 'Reading Material',
    tab_switch: 'Tab Switch',
    suspicious_activity: 'Suspicious Activity',
  };

  return labels[type] || type;
}
