'use client';

import { useEffect, useRef, useState } from 'react';
import { format } from 'date-fns';
import { Calendar as CalendarIcon, Mic, MicOff, Send, Trash2 } from 'lucide-react';
import { DayPicker } from 'react-day-picker';
import 'react-day-picker/dist/style.css';

export default function WingmanAssistant() {
  const [isRecording, setIsRecording] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [showCalendar, setShowCalendar] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      const formatted = selectedDate.toISOString().split('T')[0];
      const res = await fetch(`http://localhost:8000/conversations?date=${formatted}`);
      const data = await res.json();
      setConversations(data.conversations || []);
      setIsLoading(false);
    };

    // Prevent initial fetch if conversations are already empty
    if (conversations.length === 0) {
      fetchData();
    }
  }, [selectedDate]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversations]);

  const handleSend = async () => {
    if (!inputMessage.trim()) return;

    const user = {
      role: 'user', // Corrected from 'type' to 'role'
      content: inputMessage, // Corrected from 'message' to 'content'
      timestamp: new Date(),
    };

    setConversations((prev) => [...prev, user]);
    setInputMessage('');

    try {
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: user.content }), // Corrected from 'message' to 'content'
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      const assistant = {
        role: 'assistant', // Corrected from 'type' to 'role'
        content: data.response, // Corrected from 'message' to 'content'
        timestamp: new Date(),
      };

      setConversations((prev) => [...prev, assistant]);
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const toggleRecording = async () => {
    if (isRecording) {
      const res = await fetch('/api/voice/stop', { method: 'POST' });
      const data = await res.json();
      setInputMessage(data.transcription || '');
    } else {
      await fetch('/api/voice/start', { method: 'POST' });
    }
    setIsRecording((r) => !r);
  };

  const deleteHistory = async () => {
    const confirmDelete = confirm('Delete today’s history?');
    if (!confirmDelete) return;
    const formatted = selectedDate.toISOString().split('T')[0];
    await fetch(`http://localhost:8000/conversations?date=${formatted}`, { method: 'DELETE' });
    setConversations([]);
  };

  return (
    <div className="flex flex-col h-screen bg-white text-black font-sans">
      {/* Header */}
      <header className="flex items-center justify-between border-b px-6 py-3">
        <h1 className="text-xl font-semibold tracking-tight">Wingman</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setSelectedDate(new Date())}
            className="text-sm px-3 py-1 border border-black rounded hover:bg-black hover:text-white transition"
          >
            Today
          </button>

          <div className="relative">
            <button
              onClick={() => setShowCalendar(!showCalendar)}
              className="flex items-center gap-1 text-sm border border-black px-3 py-1 rounded hover:bg-black hover:text-white transition"
            >
              <CalendarIcon size={14} />
              {format(selectedDate, 'dd MMM')}
            </button>

            {showCalendar && (
              <div className="absolute right-0 mt-2 z-10 bg-white shadow border p-2 rounded">
                <DayPicker
                  mode="single"
                  selected={selectedDate}
                  onSelect={(date) => {
                    if (date) {
                      setSelectedDate(date);
                      setShowCalendar(false);
                    }
                  }}
                />
              </div>
            )}
          </div>

          <button onClick={deleteHistory} className="p-2 hover:text-gray-500">
            <Trash2 size={18} />
          </button>
        </div>
      </header>

      {/* Chat */}
      <main className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
        {isLoading ? (
          <p className="text-center text-gray-400">Loading...</p>
        ) : conversations.length === 0 ? (
          <p className="text-center text-gray-400 mt-10">No conversation</p>
        ) : (
          conversations.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-lg px-4 py-3 text-sm rounded-2xl shadow ${
                  msg.role === 'user'
                    ? 'bg-black text-white rounded-br-none'
                    : 'bg-gray-100 text-black border border-gray-200 rounded-bl-none'
                }`}
              >
                <p>{msg.content}</p>
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </main>

      {/* Input */}
      <footer className="border-t px-6 py-4">
        <div className="flex items-center gap-3 max-w-3xl mx-auto">
          <button
            onClick={toggleRecording}
            className={`p-3 rounded border transition ${
              isRecording ? 'bg-black text-white' : 'hover:bg-black hover:text-white'
            }`}
          >
            {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
          </button>

          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            rows={1}
            placeholder="Type a message..."
            className="flex-1 border border-gray-300 rounded p-3 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-black"
          />

          <button
            onClick={handleSend}
            disabled={!inputMessage.trim()}
            className={`p-3 rounded transition ${
              inputMessage.trim()
                ? 'bg-black text-white hover:bg-gray-900'
                : 'border border-gray-200 text-gray-300 cursor-not-allowed'
            }`}
          >
            <Send size={18} />
          </button>
        </div>
      </footer>
    </div>
  );
}