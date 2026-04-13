import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';

/**
 * 合并 Tailwind CSS 类名
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * 生成随机用户 ID
 */
export function generateUserId(): string {
  return `user_${Math.random().toString(36).substring(2, 10)}`;
}

/**
 * 生成随机会话 ID
 */
export function generateSessionId(): string {
  return `sess_${Math.random().toString(36).substring(2, 15)}`;
}

/**
 * 格式化日期时间
 */
export function formatDate(date: string | Date | undefined): string {
  if (!date) return '';
  const d = typeof date === 'string' ? new Date(date) : date;
  return format(d, 'yyyy-MM-dd HH:mm', { locale: zhCN });
}

/**
 * 格式化相对时间
 */
export function formatRelativeTime(date: string | Date | undefined): string {
  if (!date) return '';
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  
  if (minutes < 1) return '刚刚';
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 30) return `${days}天前`;
  
  return format(d, 'yyyy-MM-dd', { locale: zhCN });
}

/**
 * 截断文本
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

/**
 * 导出对话为 Markdown
 */
export function exportConversation(
  messages: Array<{ role: string; content: string }>,
  sessionId?: string
): string {
  const now = new Date();
  let content = '# 对话记录\n\n';
  content += `会话 ID: ${sessionId || 'new'}\n`;
  content += `导出时间: ${format(now, 'yyyy-MM-dd HH:mm:ss')}\n\n`;
  content += '---\n\n';

  messages.forEach((msg) => {
    const role = msg.role === 'user' ? '用户' : '助手';
    content += `**${role}**: ${msg.content}\n\n`;
  });

  return content;
}

/**
 * 下载文件
 */
export function downloadFile(content: string, filename: string, type = 'text/markdown') {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
