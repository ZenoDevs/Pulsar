import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <main className="notfound">
      <p className="mf-kicker">Pagina non trovata</p>
      <h1>Questa pagina non esiste. Almeno, nessuna testata lo conferma.</h1>
      <p>Il link potrebbe essere vecchio: le storie restano aperte per tre giorni, poi escono dall'edizione.</p>
      <div className="mf-cta">
        <Link to="/" className="onb-cta onb-cta--dark">
          Torna all'edizione
        </Link>
        <Link to="/verifica" className="btn-line">
          Verifica una notizia
        </Link>
      </div>
    </main>
  );
}
