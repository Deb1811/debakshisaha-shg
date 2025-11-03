import React, { useState } from "react";
import { Upload, FileText, TrendingUp, Users, AlertCircle, CheckCircle } from "lucide-react";

export default function Chatbot() {
  const [file, setFile] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Please select a file first!");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      setError("");
      setData(null);

      const res = await fetch("http://127.0.0.1:5000/analyze-ledger", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || "Failed to analyze ledger");
      }

      const responseData = await res.json();
      setData(responseData);
      
      // Add to history
      const historyItem = {
        id: Date.now(),
        fileName: file.name,
        timestamp: new Date().toLocaleString(),
        data: responseData
      };
      setHistory(prev => [historyItem, ...prev]);
    } catch (err) {
      setError("Error analyzing ledger: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-900 via-teal-800 to-slate-900 text-white relative overflow-hidden flex">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-80' : 'w-0'} transition-all duration-300 bg-white/5 backdrop-blur-md border-r border-white/10 flex-shrink-0 overflow-hidden`}>
        <div className="h-full flex flex-col p-4">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white">History</h2>
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto space-y-3">
            {history.length === 0 ? (
              <p className="text-white/50 text-sm text-center mt-8">No analysis history yet</p>
            ) : (
              history.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setData(item.data)}
                  className="w-full bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg p-3 text-left transition-colors"
                >
                  <p className="text-white font-semibold text-sm truncate mb-1">{item.fileName}</p>
                  <p className="text-white/50 text-xs">{item.timestamp}</p>
                  <div className="flex gap-2 mt-2 text-xs text-white/70">
                    <span>{item.data.total_members} members</span>
                    <span>•</span>
                    <span>₹{item.data.total_amount.toLocaleString()}</span>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Toggle Button */}
      {!sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(true)}
          className="fixed left-4 top-4 z-20 p-3 bg-white/10 backdrop-blur-md border border-white/20 rounded-lg hover:bg-white/20 transition-colors"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      )}

      {/* Main Content */}
      <div className="flex-1 p-8 overflow-y-auto">
        {/* Decorative Background */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-10 w-64 h-64 bg-green-400 rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-blue-400 rounded-full blur-3xl"></div>
          <div className="absolute top-1/2 left-1/3 w-72 h-72 bg-teal-400 rounded-full blur-3xl"></div>
        </div>

        <div className="relative z-10 max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-green-400 to-teal-400 rounded-xl flex items-center justify-center">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-green-300 via-teal-300 to-blue-300 text-transparent bg-clip-text">
                SHG Ledger Analyzer
              </h1>
            </div>
            <p className="text-white/70 text-lg">Upload your ledger image for AI-powered analysis</p>
          </div>

          {/* Upload Card */}
          <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl shadow-2xl p-8 mb-8 max-w-2xl mx-auto">
            <div className="space-y-6">
              <div className="border-2 border-dashed border-white/30 rounded-xl p-8 text-center hover:border-white/50 transition-colors bg-white/5">
                <Upload className="w-12 h-12 text-green-300 mx-auto mb-4" />
                <label className="cursor-pointer">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  <div className="text-white/90 mb-2">
                    {file ? (
                      <div className="flex items-center justify-center gap-2">
                        <CheckCircle className="w-5 h-5 text-green-400" />
                        <span className="font-semibold text-green-300">{file.name}</span>
                      </div>
                    ) : (
                      <>
                        <span className="font-semibold text-white">Click to upload</span>
                        <span className="text-white/60"> or drag and drop</span>
                      </>
                    )}
                  </div>
                  <p className="text-sm text-white/50">PNG, JPG or JPEG (Max 10MB)</p>
                </label>
              </div>

              <button
                onClick={handleUpload}
                disabled={loading}
                className={`w-full px-6 py-4 rounded-xl font-semibold transition-all duration-300 ${
                  loading
                    ? "bg-gray-600 cursor-not-allowed"
                    : "bg-gradient-to-r from-green-500 to-teal-500 hover:from-green-400 hover:to-teal-400 hover:shadow-lg hover:scale-105"
                }`}
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Analyzing...
                  </span>
                ) : (
                  "Upload and Analyze"
                )}
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-500/20 border border-red-500/50 backdrop-blur-md text-red-200 p-4 rounded-xl mb-8 max-w-2xl mx-auto flex items-start gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <p>{error}</p>
            </div>
          )}

          {/* Results */}
          {data && (
            <div className="space-y-8">
              {/* Summary Cards */}
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-xl p-6 hover:bg-white/15 transition-all">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-cyan-400 rounded-lg flex items-center justify-center">
                      <FileText className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="text-sm text-white/60">Language</p>
                      <p className="text-xl font-bold">{data.language}</p>
                      <p className="text-xs text-white/50">{data.confidence}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-xl p-6 hover:bg-white/15 transition-all">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-green-400 to-emerald-400 rounded-lg flex items-center justify-center">
                      <Users className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="text-sm text-white/60">Total Members</p>
                      <p className="text-xl font-bold">{data.total_members}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-xl p-6 hover:bg-white/15 transition-all">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-purple-400 to-pink-400 rounded-lg flex items-center justify-center">
                      <TrendingUp className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="text-sm text-white/60">Total Transactions</p>
                      <p className="text-xl font-bold">{data.total_transactions}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-xl p-6 hover:bg-white/15 transition-all">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-yellow-400 to-orange-400 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold">₹</span>
                    </div>
                    <div>
                      <p className="text-sm text-white/60">Total Amount</p>
                      <p className="text-xl font-bold">₹{data.total_amount.toLocaleString()}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-xl p-6 hover:bg-white/15 transition-all">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-teal-400 to-cyan-400 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-lg">S</span>
                    </div>
                    <div>
                      <p className="text-sm text-white/60">Avg SHG Score</p>
                      <p className="text-xl font-bold">{data.avg_shg_score}/100</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-xl p-6 hover:bg-white/15 transition-all">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-indigo-400 to-purple-400 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-lg">C</span>
                    </div>
                    <div>
                      <p className="text-sm text-white/60">Avg Credit Score</p>
                      <p className="text-xl font-bold">{data.avg_credit_score}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Member Analysis Table */}
              {data.member_analysis && data.member_analysis.length > 0 && (
                <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-8">
                  <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
                    <Users className="w-7 h-7 text-green-300" />
                    Member Analysis
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                      <thead>
                        <tr className="border-b border-white/20">
                          <th className="px-4 py-3 text-left font-semibold text-white/90">Member</th>
                          <th className="px-4 py-3 text-left font-semibold text-white/90">SHG</th>
                          <th className="px-4 py-3 text-left font-semibold text-white/90">Credit</th>
                          <th className="px-4 py-3 text-left font-semibold text-white/90">Behavioral</th>
                          <th className="px-4 py-3 text-left font-semibold text-white/90">Inclusion</th>
                          <th className="px-4 py-3 text-left font-semibold text-white/90">Eligibility</th>
                          <th className="px-4 py-3 text-left font-semibold text-white/90">Max Loan</th>
                          <th className="px-4 py-3 text-left font-semibold text-white/90">Ratio</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.member_analysis.map((m, idx) => (
                          <tr 
                            key={idx} 
                            className={`border-b border-white/10 hover:bg-white/5 transition-colors ${
                              idx % 2 === 0 ? 'bg-white/5' : ''
                            }`}
                          >
                            <td className="px-4 py-3 font-semibold text-white">{m.Member}</td>
                            <td className="px-4 py-3 text-white/80">{m.SHG}</td>
                            <td className="px-4 py-3 text-white/80">{m.Credit}</td>
                            <td className="px-4 py-3 text-white/80">{m.Behavioral}</td>
                            <td className="px-4 py-3 text-white/80">{m.Inclusion}</td>
                            <td className="px-4 py-3">
                              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                                m.Eligibility === 'High' ? 'bg-green-500/30 text-green-300 border border-green-500/50' :
                                m.Eligibility === 'Good' ? 'bg-blue-500/30 text-blue-300 border border-blue-500/50' :
                                m.Eligibility === 'Medium' ? 'bg-yellow-500/30 text-yellow-300 border border-yellow-500/50' :
                                'bg-red-500/30 text-red-300 border border-red-500/50'
                              }`}>
                                {m.Eligibility}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-white/80 font-semibold">₹{m.MaxLoan.toLocaleString()}</td>
                            <td className="px-4 py-3 text-white/80">{m.Ratio}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}