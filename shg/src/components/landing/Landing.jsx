import React from "react";
import { useNavigate } from "react-router-dom";

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col text-[#FEFAE0] bg-[#5F6F52]">
      {/* Header */}
      <header className="w-full py-5 px-8 flex justify-between items-center bg-white/5 backdrop-blur-md border-b border-white/10">
        <h1 className="text-2xl font-bold text-[#FEFAE0]">SHG Digitization</h1>
        <nav className="space-x-6 text-[#FEFAE0]/90">
          <a href="#about" className="hover:text-[#B99470] transition">About</a>
          <a href="#features" className="hover:text-[#B99470] transition">Features</a>
          <a href="#contact" className="hover:text-[#B99470] transition">Contact</a>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="flex flex-col items-center justify-center text-center flex-1 px-6">
        <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl shadow-lg p-10 max-w-3xl mx-auto">
          <h2 className="text-5xl font-extrabold mb-6 text-[#FEFAE0] drop-shadow-md">
            Empowering Rural SHGs through AI & OCR
          </h2>
          <p className="max-w-2xl text-lg text-[#FEFAE0]/90 mb-8">
            Our platform digitizes handwritten Self-Help Group (SHG) ledgers using Optical Character Recognition (OCR)
            and generates AI-driven credit scores to improve financial accessibility for rural communities.
          </p>
          <div className="flex flex-wrap justify-center gap-6">
            {/* Navigate to Chatbot */}
            <button
              onClick={() => navigate("/chatbot")}
              className="bg-[#A9B388] text-[#5F6F52] px-6 py-3 rounded-lg font-semibold hover:bg-[#B99470] hover:text-[#FEFAE0] transition"
            >
              Get Started
            </button>
            <button className="border border-[#FEFAE0] text-[#FEFAE0] px-6 py-3 rounded-lg font-semibold hover:bg-[#FEFAE0] hover:text-[#5F6F52] transition">
              Learn More
            </button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="text-center py-4 text-sm bg-white/5 border-t border-white/10 text-[#FEFAE0]/80">
        © {new Date().getFullYear()} SHG Digitization Project. All rights reserved.
      </footer>
    </div>
  );
}
