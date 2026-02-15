import { useState } from 'react';
import { Send } from 'lucide-react';

export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const msg = text.trim();
    if (!msg || disabled) return;
    onSend(msg);
    setText('');
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={disabled}
        placeholder={disabled ? 'Agent is thinking...' : 'Type a message...'}
        className="flex-1 rounded-xl border border-divider bg-surface px-4 py-2.5 text-sm outline-none transition focus:border-accent disabled:opacity-50"
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent text-white transition hover:bg-accent/90 disabled:opacity-40"
      >
        <Send size={16} />
      </button>
    </form>
  );
}
