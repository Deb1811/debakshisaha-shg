import React from "react";

export default function Landing() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-white to-gray-100 text-gray-800">
      {/* Header */}
      <header className="w-full py-4 px-8 flex justify-between items-center bg-white shadow-sm">
        <h1 className="text-xl font-bold text-indigo-600">MyWebsite</h1>
        <nav className="space-x-4 text-sm">
          <a href="#about" className="hover:text-indigo-600">About</a>
          <a href="#services" className="hover:text-indigo-600">Services</a>
          <a href="#contact" className="hover:text-indigo-600">Contact</a>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="flex flex-col items-center text-center mt-20 px-6">
        <h2 className="text-4xl font-extrabold mb-4">
          Welcome to <span className="text-indigo-600">MyWebsite</span>
        </h2>
        <p className="text-gray-600 max-w-md mb-6">
          A simple, clean landing page built with React and Tailwind CSS.
        </p>
        <div className="flex gap-4">
          <button className="bg-indigo-600 text-white px-5 py-2 rounded-md hover:bg-indigo-700">
            Get Started
          </button>
          <button className="border border-gray-300 px-5 py-2 rounded-md hover:bg-gray-50">
            Learn More
          </button>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-auto w-full py-4 text-center border-t text-sm text-gray-600">
        © {new Date().getFullYear()} MyWebsite. All rights reserved.
      </footer>
    </div>
  );
}
