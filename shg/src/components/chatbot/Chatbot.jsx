import React, { useState } from "react";

export default function Chatbot() {
  const [file, setFile] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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
    } catch (err) {
      setError("Error analyzing ledger: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#5F6F52] text-[#FEFAE0] p-8">
      <h1 className="text-4xl font-bold mb-6">🏦 SHG Ledger Analyzer</h1>

      <div className="bg-[#A9B388] p-6 rounded-xl shadow-lg w-full max-w-lg text-[#5F6F52]">
        <input
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          className="mb-4 w-full text-sm bg-white p-2 rounded"
        />
        <button
          onClick={handleUpload}
          disabled={loading}
          className={`w-full px-6 py-3 rounded-lg font-semibold transition ${
            loading
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-[#5F6F52] text-[#FEFAE0] hover:bg-[#4E5E44]"
          }`}
        >
          {loading ? "Analyzing..." : "Upload and Analyze"}
        </button>
      </div>

      <div className="mt-8 w-full max-w-6xl">
        {error && (
          <div className="bg-red-200 text-red-800 p-4 rounded-lg mb-4">{error}</div>
        )}

        {data && (
          <div className="bg-[#FEFAE0] text-[#5F6F52] p-6 rounded-lg shadow-lg">
            <h2 className="text-3xl font-bold mb-4 text-center">
              📊 SHG LEDGER ANALYSIS RESULTS
            </h2>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6 bg-[#A9B388] p-4 rounded-lg">
              <div>
                <p className="text-sm font-semibold">Language:</p>
                <p className="text-lg">{data.language} ({data.confidence})</p>
              </div>
              <div>
                <p className="text-sm font-semibold">Total Members:</p>
                <p className="text-lg">{data.total_members}</p>
              </div>
              <div>
                <p className="text-sm font-semibold">Total Transactions:</p>
                <p className="text-lg">{data.total_transactions}</p>
              </div>
              <div>
                <p className="text-sm font-semibold">Total Amount:</p>
                <p className="text-lg">₹{data.total_amount.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm font-semibold">Avg SHG Score:</p>
                <p className="text-lg">{data.avg_shg_score}/100</p>
              </div>
              <div>
                <p className="text-sm font-semibold">Avg Credit Score:</p>
                <p className="text-lg">{data.avg_credit_score}</p>
              </div>
            </div>

            {data.member_analysis && data.member_analysis.length > 0 && (
              <div className="mt-6">
                <h3 className="text-2xl font-bold mb-4">🎯 MEMBER ANALYSIS</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full border-2 border-[#5F6F52] text-sm">
                    <thead className="bg-[#5F6F52] text-[#FEFAE0]">
                      <tr>
                        <th className="px-4 py-3 text-left border border-[#A9B388]">Member</th>
                        <th className="px-4 py-3 text-left border border-[#A9B388]">SHG</th>
                        <th className="px-4 py-3 text-left border border-[#A9B388]">Credit</th>
                        <th className="px-4 py-3 text-left border border-[#A9B388]">Behavioral</th>
                        <th className="px-4 py-3 text-left border border-[#A9B388]">Inclusion</th>
                        <th className="px-4 py-3 text-left border border-[#A9B388]">Eligibility</th>
                        <th className="px-4 py-3 text-left border border-[#A9B388]">Max Loan</th>
                        <th className="px-4 py-3 text-left border border-[#A9B388]">Ratio</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.member_analysis.map((m, idx) => (
                        <tr 
                          key={idx} 
                          className={`border-t-2 border-[#A9B388] ${
                            idx % 2 === 0 ? 'bg-white' : 'bg-[#F5F5DC]'
                          }`}
                        >
                          <td className="px-4 py-3 font-semibold border border-[#A9B388]">{m.Member}</td>
                          <td className="px-4 py-3 border border-[#A9B388]">{m.SHG}</td>
                          <td className="px-4 py-3 border border-[#A9B388]">{m.Credit}</td>
                          <td className="px-4 py-3 border border-[#A9B388]">{m.Behavioral}</td>
                          <td className="px-4 py-3 border border-[#A9B388]">{m.Inclusion}</td>
                          <td className="px-4 py-3 border border-[#A9B388]">
                            <span className={`px-2 py-1 rounded ${
                              m.Eligibility === 'High' ? 'bg-green-200 text-green-800' :
                              m.Eligibility === 'Good' ? 'bg-blue-200 text-blue-800' :
                              m.Eligibility === 'Medium' ? 'bg-yellow-200 text-yellow-800' :
                              'bg-red-200 text-red-800'
                            }`}>
                              {m.Eligibility}
                            </span>
                          </td>
                          <td className="px-4 py-3 border border-[#A9B388]">₹{m.MaxLoan.toLocaleString()}</td>
                          <td className="px-4 py-3 border border-[#A9B388]">{m.Ratio}</td>
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
  );
}