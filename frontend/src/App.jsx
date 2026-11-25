import { BrowserRouter, Route, Routes } from "react-router-dom";
import Masthead from "./components/Masthead";
import EditionPage from "./pages/EditionPage";
import SearchPage from "./pages/SearchPage";
import SourcesPage from "./pages/SourcesPage";
import StoryPage from "./pages/StoryPage";

export default function App() {
  return (
    <BrowserRouter>
      <a href="#contenuto" className="skip">
        Vai al contenuto
      </a>
      <Masthead />
      <div id="contenuto">
        <Routes>
          <Route path="/" element={<EditionPage />} />
          <Route path="/storia/:id" element={<StoryPage />} />
          <Route path="/story/:id" element={<StoryPage />} />
          <Route path="/cerca" element={<SearchPage />} />
          <Route path="/fonti" element={<SourcesPage />} />
        </Routes>
      </div>
      <footer className="foot">
        <p>Pulsar confronta le testate, non le sostituisce: apri sempre gli articoli originali.</p>
      </footer>
    </BrowserRouter>
  );
}
