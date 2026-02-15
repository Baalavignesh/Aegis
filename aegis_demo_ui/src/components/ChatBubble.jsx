import { User, Bot, Info } from 'lucide-react';

export default function ChatBubble({ role, content }) {
  if (role === 'user') {
    return (
      <div className="flex justify-end gap-2">
        <div className="max-w-[75%] rounded-2xl rounded-br-md bg-accent px-4 py-2.5 text-white">
          <p className="text-sm whitespace-pre-wrap">{content}</p>
        </div>
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent/10">
          <User size={16} className="text-accent" />
        </div>
      </div>
    );
  }

  if (role === 'system') {
    return (
      <div className="flex justify-center">
        <div className="flex items-center gap-2 rounded-full bg-surface-hover px-4 py-1.5">
          <Info size={14} className="text-ink-faint" />
          <p className="text-xs text-ink-faint">{content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-2">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-positive/10">
        <Bot size={16} className="text-positive" />
      </div>
      <div className="max-w-[75%] rounded-2xl rounded-bl-md border border-divider bg-surface px-4 py-2.5">
        <p className="text-sm whitespace-pre-wrap">{content}</p>
      </div>
    </div>
  );
}
