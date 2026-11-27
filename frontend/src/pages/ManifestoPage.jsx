import { Link } from "react-router-dom";

export default function ManifestoPage() {
  return (
    <main className="manifesto">
      <header className="mf-hero">
        <p className="mf-kicker">Manifesto</p>
        <h1>Non ti diciamo cosa pensare. Ti facciamo vedere cosa si sa.</h1>
      </header>

      <section className="mf-body">
        <p className="mf-lede">
          Ogni giorno lo stesso fatto arriva in dieci versioni. Cambiano le parole, l'ordine, quello che si omette. Chi legge una
          testata sola vede una versione sola, e spesso non sa nemmeno di vederne una.
        </p>
        <p>
          Pulsar non scrive notizie. Legge tutte le testate, da sinistra a destra, e le mette una accanto all'altra. Poi separa quello
          che è accertato da quello che è solo detto, e da quello che è un'opinione. Il resto lo decidi tu.
        </p>

        <h2>Cinque promesse</h2>
        <ol className="mf-list">
          <li>
            <h3>Il colore indica la certezza, mai la parte</h3>
            <p>Verde vuol dire confermato da almeno due voci indipendenti. Nessun colore appartiene a un partito.</p>
          </li>
          <li>
            <h3>Le voci si contano, gli articoli no</h3>
            <p>Dieci testate dello stesso editore sono una voce. Dieci copie di un lancio d'agenzia sono una voce.</p>
          </li>
          <li>
            <h3>Ogni fatto ha una frase dietro</h3>
            <p>L'intelligenza artificiale lavora solo sugli articoli e deve citarli parola per parola. Se una citazione non esiste, il fatto scende.</p>
          </li>
          <li>
            <h3>Le regole sono pubbliche</h3>
            <p>
              Come decidiamo che un fatto è confermato, chi possiede ogni testata, dove possiamo sbagliare: è tutto nella pagina{" "}
              <Link to="/fonti">Metodo</Link> e nel codice.
            </p>
          </li>
          <li>
            <h3>Non ti seguiamo</h3>
            <p>Nessun account, nessun tracciamento pubblicitario. I tuoi argomenti e le tue letture restano sul tuo dispositivo.</p>
          </li>
        </ol>

        <h2 id="privacy">Privacy, in chiaro</h2>
        <ul className="mf-privacy">
          <li>I tuoi argomenti, le storie che segui e lo specchio sono salvati solo nel tuo browser.</li>
          <li>Per ordinare l'edizione mandiamo al server una copia del profilo a ogni apertura. Il server non la conserva.</li>
          <li>Le frasi che verifichi e le domande che fai non vengono salvate.</li>
          <li>Puoi cancellare tutto dalla pagina Argomenti, o svuotando i dati del sito nel browser.</li>
        </ul>

        <h2>Dove possiamo sbagliare</h2>
        <p>
          L'orientamento delle testate è una stima, e l'asse sinistra-destra semplifica. Il raggruppamento degli articoli può unire
          due fatti vicini o separarne uno. L'intelligenza artificiale può leggere male una frase: per questo ogni stato è controllato da
          regole fisse che possono solo abbassarlo, e ogni fatto porta le sue fonti. Apri sempre gli articoli originali.
        </p>

        <div className="mf-cta">
          <Link to="/" className="onb-cta onb-cta--dark">
            Apri l'edizione di oggi
          </Link>
          <Link to="/verifica" className="btn-line">
            Verifica una notizia
          </Link>
        </div>
      </section>
    </main>
  );
}
