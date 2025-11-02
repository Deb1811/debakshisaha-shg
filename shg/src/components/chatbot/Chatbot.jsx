import React, { useState } from "react";

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hello! How can I help you today?" },
  ]);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (input.trim() === "") return;

    const newMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, newMessage]);

    // Placeholder bot reply (you can connect API later)
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Thanks for your message! I'm still learning 😊" },
      ]);
    }, 600);

    setInput("");
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#5F6F52] text-[#FEFAE0] p-6">
      <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl shadow-lg w-full max-w-md flex flex-col h-[600px]">
        {/* Header */}
        <div className="p-4 border-b border-white/20 text-center font-semibold text-[#FEFAE0] bg-white/5">
          SHG Assistant 🤖
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${
                msg.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`px-4 py-2 rounded-xl max-w-[80%] ${
                  msg.sender === "user"
                    ? "bg-[#A9B388] text-[#5F6F52]"
                    : "bg-[#B99470]/50 text-[#FEFAE0]"
                }`}
              >
                {msg.text}
              </div>
            </div>
          ))}
        </div>

        {/* Input Box */}
        <div className="flex items-center p-3 border-t border-white/20 bg-white/5">
          <input
            type="text"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            className="flex-1 bg-transparent outline-none px-3 text-[#FEFAE0] placeholder-[#FEFAE0]/60"
          />
          <button
            onClick={handleSend}
            className="ml-3 bg-[#A9B388] text-[#5F6F52] px-4 py-2 rounded-lg font-semibold hover:bg-[#B99470] transition"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
