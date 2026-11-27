import { BrowserRouter, Link, Route, Routes, useLocation } from "react-router-dom";
import Masthead from "./components/Masthead";
import Briefing from "./pages/Briefing";
import Home from "./pages/Home";
import Onboarding from "./pages/Onboarding";
import SearchPage from "./pages/SearchPage";
import SourcesPage from "./pages/SourcesPage";
import StoryPage from "./pages/StoryPage";
import TopicsPage from "./pages/TopicsPage";
import VerifyPage from "./pages/VerifyPage";
import MirrorPage from "./pages/MirrorPage";
import ManifestoPage from "./pages/ManifestoPage";
import NotFound from "./pages/NotFound";

/** Briefing e onboarding sono esperienze a schermo intero: niente testata né piede. */
function Shell() {
  const { pathname } = useLocation();
  const immersive = pathname.startsWith("/briefing") || pathname.startsWith("/benvenuto");
  return (
    <>
      <a href="#contenuto" className="skip">
        Vai al contenuto
      </a>
      {!immersive && <Masthead />}
      <div id="contenuto">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/benvenuto" element={<Onboarding />} />
          <Route path="/briefing" element={<Briefing />} />
          <Route path="/argomenti" element={<TopicsPage />} />
          <Route path="/storia/:id" element={<StoryPage />} />
          <Route path="/story/:id" element={<StoryPage />} />
          <Route path="/cerca" element={<SearchPage />} />
          <Route path="/fonti" element={<SourcesPage />} />
          <Route path="/verifica" element={<VerifyPage />} />
          <Route path="/specchio" element={<MirrorPage />} />
          <Route path="/manifesto" element={<ManifestoPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
      {!immersive && (
        <footer className="foot">
          <p>Pulsar confronta le testate, non le sostituisce: apri sempre gli articoli originali.</p>
          <nav className="foot-nav" aria-label="Informazioni">
            <Link to="/manifesto">Manifesto</Link>
            <Link to="/fonti">Metodo e fonti</Link>
            <Link to="/manifesto#privacy">Privacy</Link>
            <a href="https://github.com/ZenoDevs/Pulsar" target="_blank" rel="noreferrer">
              Codice
            </a>
          </nav>
        </footer>
      )}
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Shell />
    </BrowserRouter>
  );
}
