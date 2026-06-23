// components/dashboard/MessageBubble.tsx — All message type renderers

import {
  FileText,
  Image as ImageIcon,
  Download,
  Mic,
  Video,
  MapPin,
  Sticker,
  MessageCircle,
  AlertCircle,
} from 'lucide-react';
import type { Message } from '../../types';

interface Props {
  message: Message;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function DeliveryTicks({ status }: { status: string | null | undefined }) {
  if (!status) return null;
  if (status === 'read') return <span className="text-blue-400 text-[10px] ml-1">✓✓</span>;
  if (status === 'delivered') return <span className="text-gray-400 text-[10px] ml-1">✓✓</span>;
  if (status === 'sent') return <span className="text-gray-500 text-[10px] ml-1">✓</span>;
  if (status === 'failed') return <span className="text-status-human text-[10px] ml-1">✗</span>;
  return null;
}

function ExpiredMedia({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 text-gray-500">
      <AlertCircle size={14} />
      <span className="text-xs">{label} unavailable or expired</span>
    </div>
  );
}

function docIcon(mime: string | null) {
  if (mime?.includes('pdf')) return { icon: FileText, color: 'text-red-400', bg: 'bg-red-500/20', label: 'PDF' };
  if (mime?.includes('sheet') || mime?.includes('excel'))
    return { icon: FileText, color: 'text-green-400', bg: 'bg-green-500/20', label: 'Spreadsheet' };
  return { icon: FileText, color: 'text-blue-400', bg: 'bg-blue-500/20', label: 'Document' };
}

export function MessageBubble({ message }: Props) {
  const isBot = message.direction === 'outbound';
  const isTyping = message.message_type === 'typing_indicator';
  const isSystem = message.message_type === 'system';

  const bubbleLayout = (content: React.ReactNode) => (
    <div className={`flex ${isBot ? 'justify-end' : 'justify-start'} mb-3 animate-slide-up`}>
      <div className={`flex items-end gap-2 max-w-[85%] md:max-w-[75%] ${isBot ? 'flex-row-reverse' : ''}`}>
        {isBot ? <BotAvatar /> : <UserAvatar phone={message.sender} />}
        <div className="flex flex-col gap-1 min-w-0">
          {content}
          <span className={`text-[10px] text-gray-600 px-1 flex items-center ${isBot ? 'justify-end' : ''}`}>
            {formatTime(message.timestamp)}
            {isBot && message.message_type !== 'typing_indicator' && (
              <DeliveryTicks status={message.delivery_status} />
            )}
          </span>
        </div>
      </div>
    </div>
  );

  if (isTyping) {
    return (
      <div className="flex justify-start mb-3 animate-fade-in">
        <div className="flex items-end gap-2">
          <BotAvatar />
          <div className="flex flex-col gap-1">
            <div className="bubble-media px-4 py-2.5 flex items-center gap-1.5">
              <span className="text-[10px] text-gray-400 mr-1">was typing</span>
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="w-1 h-1 rounded-full bg-gray-500 typing-dot animate-pulse-dot"
                />
              ))}
            </div>
            <span className="text-[10px] text-gray-600 px-1">{formatTime(message.timestamp)}</span>
          </div>
        </div>
      </div>
    );
  }

  if (isSystem) {
    return (
      <div className="flex justify-center mb-3">
        <span className="text-[10px] text-gray-500 bg-surface-elevated px-3 py-1 rounded-full">
          {message.text_content}
        </span>
      </div>
    );
  }

  if (message.message_type === 'image') {
    if (!message.media_url) {
      return bubbleLayout(
        <div className={`${isBot ? 'bubble-media' : 'bubble-user'} p-3`}>
          <ExpiredMedia label="Image" />
        </div>,
      );
    }
    return bubbleLayout(
      <div className={`${isBot ? 'bubble-media' : 'bubble-user'} overflow-hidden rounded-2xl`}>
        <a href={message.media_url} target="_blank" rel="noopener noreferrer">
          <img
            src={message.media_url}
            alt="Shared"
            className="max-w-[260px] max-h-[200px] object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        </a>
        {message.text_content && <p className="text-sm text-gray-200 px-3 py-2">{message.text_content}</p>}
        <div className="px-3 pb-2 flex items-center gap-1">
          <ImageIcon size={10} className="text-indigo-400" />
          <span className="text-[10px] text-indigo-400">Image</span>
        </div>
      </div>,
    );
  }

  if (message.message_type === 'document') {
    const doc = docIcon(message.media_mime_type);
    const DocIcon = doc.icon;
    if (!message.media_url) {
      return bubbleLayout(
        <div className={`${isBot ? 'bubble-media' : 'bubble-user'} p-3`}>
          <ExpiredMedia label="Document" />
        </div>,
      );
    }
    return bubbleLayout(
      <div className={`${isBot ? 'bubble-media' : 'bubble-user'} p-3`}>
        <div className="flex items-center gap-3 mb-2">
          <div className={`w-10 h-10 rounded-lg ${doc.bg} flex items-center justify-center flex-shrink-0`}>
            <DocIcon size={18} className={doc.color} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">
              {message.media_filename || 'Document'}
            </p>
            <p className="text-[10px] text-gray-500">{doc.label}</p>
          </div>
        </div>
        {message.text_content && <p className="text-sm text-gray-300 mb-2">{message.text_content}</p>}
        <a
          href={message.media_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 text-xs text-brand-primary hover:text-brand-glow"
        >
          <Download size={12} />
          Download
        </a>
      </div>,
    );
  }

  if (message.message_type === 'audio') {
    return bubbleLayout(
      <div className={`${isBot ? 'bubble-media' : 'bubble-user'} p-3 min-w-[200px]`}>
        <div className="flex items-center gap-2 mb-2">
          <Mic size={16} className="text-brand-glow" />
          <span className="text-xs text-gray-300">Voice message</span>
        </div>
        {message.media_url ? (
          <audio controls src={message.media_url} className="w-full h-8" />
        ) : (
          <ExpiredMedia label="Audio" />
        )}
      </div>,
    );
  }

  if (message.message_type === 'video') {
    return bubbleLayout(
      <div className={`${isBot ? 'bubble-media' : 'bubble-user'} overflow-hidden rounded-2xl p-1`}>
        <div className="flex items-center gap-1 px-2 py-1">
          <Video size={12} className="text-purple-400" />
          <span className="text-[10px] text-purple-400">Video</span>
        </div>
        {message.media_url ? (
          <video controls src={message.media_url} className="max-w-[260px] max-h-[200px] rounded-lg" />
        ) : (
          <ExpiredMedia label="Video" />
        )}
        {message.text_content && <p className="text-sm text-gray-200 px-2 py-1">{message.text_content}</p>}
      </div>,
    );
  }

  if (message.message_type === 'sticker') {
    return bubbleLayout(
      <div className={`${isBot ? 'bubble-media' : 'bubble-user'} p-3`}>
        {message.media_url ? (
          <img src={message.media_url} alt="Sticker" className="w-24 h-24 object-contain" />
        ) : (
          <div className="flex items-center gap-2 text-gray-400">
            <Sticker size={20} />
            <span className="text-xs">Sticker</span>
          </div>
        )}
      </div>,
    );
  }

  if (message.message_type === 'location') {
    return bubbleLayout(
      <div className={`${isBot ? 'bubble-media' : 'bubble-user'} p-3`}>
        <div className="flex items-center gap-2 text-gray-300">
          <MapPin size={16} className="text-red-400" />
          <span className="text-sm">{message.text_content || 'Shared location'}</span>
        </div>
      </div>,
    );
  }

  if (message.message_type === 'interactive' || message.message_type === 'template') {
    return bubbleLayout(
      <div className={`${isBot ? 'bubble-media' : 'bubble-user'} p-3`}>
        <div className="flex items-center gap-2 mb-1">
          <MessageCircle size={14} className="text-brand-glow" />
          <span className="text-[10px] text-gray-500 uppercase">{message.message_type}</span>
        </div>
        <p className="text-sm text-white">{message.text_content || '(interactive message)'}</p>
      </div>,
    );
  }

  return bubbleLayout(
    <div className={`${isBot ? 'bubble-bot' : 'bubble-user'} px-4 py-2.5`}>
      <p className="text-sm text-white leading-relaxed whitespace-pre-wrap">
        {message.text_content || ''}
      </p>
    </div>,
  );
}

function BotAvatar() {
  return (
    <div className="w-7 h-7 rounded-full bg-gradient-to-br from-brand-primary to-brand-secondary flex items-center justify-center flex-shrink-0 mb-4">
      <span className="text-[10px] font-bold text-white">AI</span>
    </div>
  );
}

function UserAvatar({ phone }: { phone: string }) {
  return (
    <div className="w-7 h-7 rounded-full bg-surface-elevated border border-surface-border flex items-center justify-center flex-shrink-0 mb-4">
      <span className="text-[10px] font-medium text-gray-400">{phone.slice(-2)}</span>
    </div>
  );
}
