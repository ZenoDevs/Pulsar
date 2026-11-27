import { useEffect, useState } from "react";

/** Anteprima della scheda da condividere, quando il download non è permesso. */
export default function ImagePreview() {
  const [img, setImg] = useState(null);
  useEffect(() => {
    const on = (e) => setImg(e.detail);
    window.addEventListener("pulsar:preview", on);
    return () => window.removeEventListener("pulsar:preview", on);
  }, []);
  useEffect(() => {
    if (!img) return;
    const onKey = (e) => e.key === "Escape" && setImg(null);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [img]);
  if (!img) return null;
  return (
    <div className="preview" role="dialog" aria-modal="true" aria-label="Scheda da condividere" onClick={() => setImg(null)}>
      <figure onClick={(e) => e.stopPropagation()}>
        <img src={img.url} alt="Scheda da condividere generata da Pulsar" />
        <figcaption>
          Ecco la scheda che Pulsar genera per i social. Nell'app vera parte il foglio di condivisione del telefono; qui puoi salvarla
          con il tasto destro o tenendo premuto.
          <button className="btn-line btn-line--light" onClick={() => setImg(null)}>
            Chiudi
          </button>
        </figcaption>
      </figure>
    </div>
  );
}
