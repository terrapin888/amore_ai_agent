/**
 * AI 채팅 페이지 컴포넌트
 * 라네즈 랭킹 분석 AI 에이전트와 대화해요.
 *
 * @module components/AIChat
 */

import { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Plus, Loader2 } from 'lucide-react';
import { sendChatMessage } from '../services/api';

/**
 * 채팅 메시지 인터페이스
 *
 * @interface Message
 * @property {number} id 메시지 고유 ID
 * @property {'ai' | 'user'} type 메시지 유형 (AI 응답 또는 사용자 입력)
 * @property {string} content 메시지 내용
 */
interface Message {
  id: number;
  type: 'ai' | 'user';
  content: string;
}

/**
 * 채팅 세션 인터페이스
 *
 * @interface ChatSession
 * @property {number} id 세션 고유 ID
 * @property {string} title 세션 제목 (첫 메시지 기반)
 * @property {string} time 생성 시간
 * @property {Message[]} messages 세션 내 메시지 목록
 */
interface ChatSession {
  id: number;
  title: string;
  time: string;
  messages: Message[];
}

/**
 * 초기 AI 인사 메시지
 * @constant {Message}
 */
const initialMessage: Message = {
  id: 1,
  type: 'ai',
  content: '안녕하세요! 라네즈 글로벌 랭킹 분석 에이전트입니다.\n궁금하신 점을 질문해주세요.\n\n예시 질문:\n- 립 슬리핑 마스크 순위가 왜 높아?\n- 스킨케어 카테고리 성과 분석해줘\n- 경쟁사와 비교해줘',
};

/**
 * AI 채팅 메인 컴포넌트
 *
 * @description
 * - 대화 기록 사이드바
 * - 실시간 AI 응답 채팅
 * - 새 대화 생성 기능
 *
 * @returns {JSX.Element} AI 채팅 화면
 *
 * @example
 * <AIChat />
 */
export function AIChat() {
  const [messages, setMessages] = useState<Message[]>([initialMessage]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatSession[]>([
    { id: 1, title: '새 대화', time: '지금', messages: [initialMessage] }
  ]);
  const [currentChatId, setCurrentChatId] = useState(1);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  /**
   * 채팅 스크롤을 맨 아래로 이동해요.
   */
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  /**
   * 메시지를 전송하고 AI 응답을 받아요.
   *
   * @returns {Promise<void>}
   */
  async function handleSend() {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: messages.length + 1,
      type: 'user',
      content: inputValue.trim()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await sendChatMessage(userMessage.content);

      const aiMessage: Message = {
        id: messages.length + 2,
        type: 'ai',
        content: response.response
      };

      setMessages(prev => [...prev, aiMessage]);

      setChatHistory(prev => prev.map(chat =>
        chat.id === currentChatId
          ? {
              ...chat,
              title: userMessage.content.slice(0, 20) + (userMessage.content.length > 20 ? '...' : ''),
              messages: [...chat.messages, userMessage, aiMessage]
            }
          : chat
      ));

    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        id: messages.length + 2,
        type: 'ai',
        content: '죄송합니다. 서버 연결에 문제가 있습니다. 잠시 후 다시 시도해주세요.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyPress(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleNewChat() {
    const newId = chatHistory.length + 1;
    const newChat: ChatSession = {
      id: newId,
      title: '새 대화',
      time: '지금',
      messages: [initialMessage]
    };
    setChatHistory(prev => [newChat, ...prev]);
    setCurrentChatId(newId);
    setMessages([initialMessage]);
  }

  function selectChat(chatId: number) {
    const chat = chatHistory.find(c => c.id === chatId);
    if (chat) {
      setCurrentChatId(chatId);
      setMessages(chat.messages);
    }
  }

  return (
    <div className="flex h-full">
      {/* Chat History Sidebar */}
      <div className="w-80 bg-white border-r flex flex-col">
        <div className="p-6 border-b">
          <h2 className="text-xl">대화 기록</h2>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          {chatHistory.map((chat) => (
            <button
              key={chat.id}
              onClick={() => selectChat(chat.id)}
              className={`w-full text-left p-4 rounded-lg transition-colors mb-2 ${
                currentChatId === chat.id
                  ? 'bg-blue-50'
                  : 'hover:bg-gray-50'
              }`}
            >
              <p className="text-sm mb-1 truncate">{chat.title}</p>
              <p className="text-xs text-gray-500">{chat.time}</p>
            </button>
          ))}
        </div>
        <div className="p-4 border-t">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-[#1F5795] text-white rounded-lg hover:bg-[#001C58] transition-colors"
          >
            <Plus className="w-5 h-5" />
            새 대화
          </button>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="p-6 border-b bg-white">
          <h1 className="text-2xl">AI 인사이트 채팅</h1>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-2xl px-6 py-4 rounded-2xl ${
                  message.type === 'user'
                    ? 'bg-[#1F5795] text-white'
                    : 'bg-[#F1F3F4] text-gray-900'
                }`}
              >
                <p className="whitespace-pre-line">{message.content}</p>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="max-w-2xl px-6 py-4 rounded-2xl bg-[#F1F3F4]">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>분석 중...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 bg-white border-t">
          <div className="flex items-center gap-3">
            <button className="p-3 hover:bg-gray-100 rounded-full transition-colors">
              <Paperclip className="w-5 h-5 text-gray-600" />
            </button>
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="메시지를 입력하세요..."
              disabled={isLoading}
              className="flex-1 px-6 py-3 bg-gray-100 rounded-3xl focus:outline-none focus:ring-2 focus:ring-[#1F5795] disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !inputValue.trim()}
              className="p-3 bg-[#1F5795] text-white rounded-full hover:bg-[#001C58] transition-colors disabled:opacity-50"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
