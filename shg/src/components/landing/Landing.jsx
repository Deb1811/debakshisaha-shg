import React from "react";
import { useNavigate } from "react-router-dom";
import { Sprout, Users, TrendingUp, BookOpen } from "lucide-react";

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col text-white bg-gradient-to-br from-emerald-900 via-teal-800 to-slate-900 relative overflow-hidden">
      {/* Decorative Background Elements */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-20 left-10 w-64 h-64 bg-green-400 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-blue-400 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/3 w-72 h-72 bg-teal-400 rounded-full blur-3xl"></div>
      </div>

      {/* Subtle Pattern Overlay */}
      <div className="absolute inset-0 opacity-5" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
      }}></div>

      <div className="relative z-10 flex flex-col min-h-screen">
        {/* Header */}
        <header className="w-full py-6 px-8 flex justify-between items-center bg-black/20 backdrop-blur-md border-b border-white/10">
          <div className="flex items-center gap-3">
            <Sprout className="w-8 h-8 text-green-300" />
            <h1 className="text-2xl font-bold text-white">SHG Digitization</h1>
          </div>
          <nav className="space-x-6 text-white/90 hidden md:flex">
            <a href="#about" className="hover:text-green-300 transition">About</a>
            <a href="#features" className="hover:text-green-300 transition">Features</a>
            <a href="#contact" className="hover:text-green-300 transition">Contact</a>
          </nav>
        </header>

        {/* Hero Section */}
        <main className="flex flex-col items-center justify-center text-center flex-1 px-6 py-12">
          <div className="max-w-4xl mx-auto">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 bg-green-500/20 border border-green-400/30 rounded-full px-4 py-2 mb-6 backdrop-blur-sm">
              <Users className="w-4 h-4 text-green-300" />
              <span className="text-sm text-green-200">Empowering Rural Communities</span>
            </div>

            <h2 className="text-5xl md:text-6xl font-extrabold mb-6 text-white drop-shadow-2xl leading-tight">
              Empowering Rural SHGs through{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-300 via-teal-300 to-blue-300">
                AI & OCR
              </span>
            </h2>
            
            <p className="max-w-2xl mx-auto text-lg text-white/80 mb-10 leading-relaxed">
              Our platform digitizes handwritten Self-Help Group ledgers using advanced OCR technology
              and generates AI-driven credit scores to improve financial accessibility for rural communities.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-wrap justify-center gap-4 mb-16">
              <button
                onClick={() => navigate("/chatbot")}
                className="group relative bg-gradient-to-r from-green-500 to-teal-500 text-white px-8 py-4 rounded-xl font-semibold shadow-lg hover:shadow-2xl hover:scale-105 transition-all duration-300"
              >
                <span className="relative z-10">Get Started</span>
                <div className="absolute inset-0 bg-gradient-to-r from-green-400 to-teal-400 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 blur"></div>
              </button>
              <button className="border-2 border-white/30 bg-white/10 backdrop-blur-sm text-white px-8 py-4 rounded-xl font-semibold hover:bg-white/20 hover:border-white/50 transition-all duration-300">
                Learn More
              </button>
            </div>

            {/* Feature Cards */}
            <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
              <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-6 hover:bg-white/15 transition-all duration-300 hover:scale-105">
                <div className="w-12 h-12 bg-gradient-to-br from-green-400 to-teal-400 rounded-lg flex items-center justify-center mb-4 mx-auto">
                  <BookOpen className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold mb-2 text-white">OCR Technology</h3>
                <p className="text-white/70 text-sm">
                  Transform handwritten ledgers into digital records with high accuracy
                </p>
              </div>

              <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-6 hover:bg-white/15 transition-all duration-300 hover:scale-105">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-cyan-400 rounded-lg flex items-center justify-center mb-4 mx-auto">
                  <TrendingUp className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold mb-2 text-white">AI Credit Scoring</h3>
                <p className="text-white/70 text-sm">
                  Generate intelligent credit scores to unlock financial opportunities
                </p>
              </div>

              <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-6 hover:bg-white/15 transition-all duration-300 hover:scale-105">
                <div className="w-12 h-12 bg-gradient-to-br from-teal-400 to-emerald-400 rounded-lg flex items-center justify-center mb-4 mx-auto">
                  <Users className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold mb-2 text-white">Community Impact</h3>
                <p className="text-white/70 text-sm">
                  Empower rural women and strengthen grassroots economies
                </p>
              </div>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="text-center py-6 text-sm bg-black/20 backdrop-blur-sm border-t border-white/10 text-white/70">
          <p>© {new Date().getFullYear()} SHG Digitization Project. All rights reserved.</p>
          <p className="text-xs mt-2 text-white/50">Building bridges between tradition and technology</p>
        </footer>
      </div>
    </div>
  );
}