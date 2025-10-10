import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import About from "./pages/About";
import Foodbanks from "./pages/Foodbanks";
import Programs from "./pages/Programs";
import Sponsors from "./pages/Sponsors";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/foodbanks" element={<Foodbanks />} />
        <Route path="/programs" element={<Programs />} />
        <Route path="/sponsors" element={<Sponsors />} />
      </Routes>
    </Router>
  );
}

export default App;
