"""Modalita' dimostrativa.

Testate, luoghi, persone e fatti qui sotto sono INVENTATI. Servono a far
vedere l'interfaccia e l'intera pipeline (regole di indipendenza, metriche,
punti ciechi) senza chiavi API e senza attribuire articoli falsi a testate
reali. L'interfaccia mostra sempre un avviso quando l'edizione e' demo.

I dossier sono scritti nello stesso formato JSON che produce il modello e
passano da ``parse_dossier``: le regole deterministiche vengono applicate
davvero (es. il fatto F5 della storia sul ponte viene declassato perche' le
due testate che lo "confermano" hanno lo stesso editore).
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import List

from .analysis.dossier import parse_dossier
from .analysis.independence import detect_echoes
from .clustering import _compute_stats
from .pipeline import STORY_CACHE, assemble_edition, finalize_story
from .schemas import Article, Edition, Story, StoryUpdate
from .sources import SourceInfo, get_source, register_sources

DEMO_SOURCES = [
    SourceInfo("demo_lince", "Agenzia Lince", "agenzia", 0.0, "Cooperativa Lince", "lince", "#",
               note="Testata inventata (demo)."),
    SourceInfo("demo_cronache", "Cronache Aperte", "online", -0.7, "Cooperativa Cronache", "cronache", "#",
               note="Testata inventata (demo)."),
    SourceInfo("demo_faro", "Il Faro", "quotidiano", -0.45, "Gruppo Aurora", "aurora", "#",
               ownership_verified=True, note="Testata inventata (demo). Stesso editore del Corriere di Vetro."),
    SourceInfo("demo_pendolo", "Il Pendolo", "quotidiano", 0.05, "Editrice Pendolo", "pendolo", "#",
               note="Testata inventata (demo)."),
    SourceInfo("demo_tgvalle", "TG Valle", "tv", 0.1, "Emittente pubblica regionale", "pubblica", "#",
               note="Testata inventata (demo)."),
    SourceInfo("demo_vetro", "Corriere di Vetro", "quotidiano", 0.35, "Gruppo Aurora", "aurora", "#",
               ownership_verified=True, note="Testata inventata (demo). Stesso editore del Faro."),
    SourceInfo("demo_baluardo", "Il Baluardo", "quotidiano", 0.75, "Holding Torre", "torre", "#",
               note="Testata inventata (demo)."),
    SourceInfo("demo_megafono", "Il Megafono", "online", 0.85, "Holding Torre", "torre", "#",
               note="Testata inventata (demo)."),
]

LINCE_PONTE = (
    "Alle 6.40 di questa mattina è crollata una campata del ponte sul fiume Serra, lungo la strada statale 14 "
    "all'ingresso di Borgo Alto. Secondo i vigili del fuoco una persona, il conducente di un furgone, è rimasta "
    "ferita in modo non grave ed è stata portata all'ospedale di Valdora. La statale è chiusa in entrambe le "
    "direzioni e il traffico viene deviato sulla provinciale 9. La Procura di Valdora ha aperto un fascicolo."
)

STORIES = [
    {
        "hours": 3,
        "articles": [
            ("demo_lince", 4.2, "Crolla campata del ponte sul Serra a Borgo Alto, un ferito", LINCE_PONTE),
            ("demo_pendolo", 3.9, "Borgo Alto, crollo sul ponte del Serra: un ferito, statale chiusa",
             LINCE_PONTE + " Sul posto anche la sindaca Elena Marchi."),
            ("demo_tgvalle", 3.8, "Ponte sul Serra, cede una campata: statale 14 chiusa",
             LINCE_PONTE.replace("questa mattina", "stamattina")),
            ("demo_faro", 3.1, "Il ponte che tutti sapevano fragile",
             "Il crollo di stamattina a Borgo Alto non è un fulmine a ciel sereno. Una relazione tecnica del 2024, "
             "che Il Faro ha potuto leggere, segnalava 'ammaloramenti significativi' dei piloni e raccomandava interventi "
             "entro dodici mesi. I lavori non sono mai partiti. Un uomo è rimasto ferito. È una tragedia annunciata, "
             "e la Regione dovrà spiegare perché quelle carte sono rimaste in un cassetto."),
            ("demo_vetro", 2.9, "Ponte del Serra, la relazione del 2024 chiedeva lavori urgenti",
             "Secondo una relazione tecnica del 2024 i piloni del ponte sul Serra presentavano ammaloramenti e "
             "andavano consolidati entro un anno. L'intervento non è stato eseguito. La Regione sostiene di aver "
             "stanziato i fondi nel 2025 e attribuisce il ritardo all'iter autorizzativo."),
            ("demo_cronache", 2.6, "Borgo Alto, il ponte della vergogna: anni di tagli alla manutenzione",
             "Il ponte della vergogna è crollato. Da tre anni la giunta regionale taglia i capitoli di spesa per la "
             "manutenzione stradale, e la relazione del 2024 lo diceva chiaramente: interventi urgenti sui piloni. "
             "Il ferito è il conducente di un furgone. Chi pagerà per questa incuria?"),
            ("demo_baluardo", 2.2, "Ponte crollato, la Regione: fondi stanziati, lavori bloccati dai vincoli",
             "La Regione Valdora fa sapere di aver stanziato 2,1 milioni di euro nel 2025 per il ponte sul Serra. "
             "Secondo l'assessore alle Infrastrutture, i lavori sono stati bloccati per mesi dal parere della "
             "Soprintendenza e dai vincoli ambientali sull'alveo del fiume. Una persona ferita, nessuna in pericolo di vita."),
            ("demo_megafono", 1.5, "Strage sfiorata a Borgo Alto: tre feriti, e i burocrati dormono",
             "Strage sfiorata sul Serra: tre persone ferite, tra cui due operai che lavoravano sotto la campata, "
             "secondo quanto riferiscono fonti locali. Ambientalisti e Soprintendenza hanno tenuto fermi i lavori per "
             "mesi. Secondo indiscrezioni, la ditta incaricata della manutenzione sarebbe già sotto indagine."),
        ],
        "llm": {
            "titolo_neutro": "Crolla una campata del ponte sul Serra a Borgo Alto, statale 14 chiusa",
            "sezione": "Cronaca",
            "sommario": "Alle 6.40 è crollata una campata del ponte sul fiume Serra a Borgo Alto. La statale 14 è chiusa e la Procura di Valdora ha aperto un fascicolo. Il numero dei feriti non è concorde tra le fonti.",
            "fatti": [
                {"testo": "Una campata del ponte sul fiume Serra, sulla statale 14, è crollata alle 6.40.", "stato": "confermato", "fonti": [1, 4, 7, 8], "evidenze": [
                    {"fonte": 1, "citazione": "Alle 6.40 di questa mattina è crollata una campata del ponte sul fiume Serra"},
                    {"fonte": 4, "citazione": "Il crollo di stamattina a Borgo Alto non è un fulmine a ciel sereno"},
                    {"fonte": 7, "citazione": "stanziato 2,1 milioni di euro nel 2025 per il ponte sul Serra"}]},
                {"testo": "La statale 14 è chiusa in entrambe le direzioni; il traffico è deviato sulla provinciale 9.", "stato": "confermato", "fonti": [1, 2, 3]},
                {"testo": "Numero dei feriti.", "stato": "contestato", "fonti": [1, 7, 8], "evidenze": [
                    {"fonte": 1, "citazione": "una persona, il conducente di un furgone, è rimasta ferita in modo non grave"},
                    {"fonte": 8, "citazione": "tre persone ferite, tra cui due operai che lavoravano sotto la campata"}], "nota": "Uno secondo vigili del fuoco e Regione, tre secondo 'fonti locali' citate da una sola testata."},
                {"testo": "La Procura di Valdora ha aperto un fascicolo.", "stato": "confermato", "fonti": [1, 2, 3]},
                {"testo": "Una relazione tecnica del 2024 raccomandava interventi sui piloni entro dodici mesi.", "stato": "confermato", "fonti": [4, 5]},
                {"testo": "La Regione ha stanziato 2,1 milioni di euro per il ponte nel 2025.", "stato": "riportato", "fonti": [7, 5], "nota": "Dichiarazione della Regione, nessun documento citato."},
                {"testo": "La ditta di manutenzione sarebbe sotto indagine.", "stato": "non_verificato", "fonti": [8], "evidenze": [
                    {"fonte": 8, "citazione": "la ditta incaricata della manutenzione sarebbe già sotto indagine"}]},
                {"testo": "Il presidente della Regione ha annunciato una commissione d'inchiesta.", "stato": "riportato", "fonti": [7], "evidenze": [
                    {"fonte": 7, "citazione": "il presidente della Regione ha annunciato una commissione d'inchiesta sul crollo"}]},
            ],
            "interpretazioni": [
                {"testo": "Il crollo è conseguenza dei tagli alla manutenzione decisi dalla giunta regionale.", "tipo": "causa", "fonti": [6]},
                {"testo": "Il crollo era prevedibile e la Regione ha ignorato gli avvertimenti.", "tipo": "giudizio", "fonti": [4]},
                {"testo": "Il ritardo dei lavori è colpa di Soprintendenza e vincoli ambientali.", "tipo": "attribuzione", "fonti": [7, 8]},
            ],
            "divergenze": [
                {"tema": "Quante persone sono rimaste ferite", "versioni": [
                    {"racconto": "Una persona, il conducente di un furgone, ferita in modo non grave.", "fonti": [1, 7]},
                    {"racconto": "Tre feriti, tra cui due operai sotto la campata.", "fonti": [8]},
                ]},
                {"tema": "Perché i lavori non sono partiti", "versioni": [
                    {"racconto": "Tagli alla spesa per la manutenzione.", "fonti": [6]},
                    {"racconto": "Iter autorizzativo, parere della Soprintendenza e vincoli ambientali.", "fonti": [5, 7, 8]},
                ]},
            ],
            "inquadramenti": [
                {"etichetta": "Responsabilità politica", "cornice": "Il crollo come prova di incuria e tagli della giunta.", "parole_chiave": ["vergogna", "tagli", "incuria", "tragedia annunciata"], "fonti": [4, 6]},
                {"etichetta": "Cronaca dei fatti", "cornice": "Ricostruzione di orari, viabilità e indagine, senza attribuzioni.", "parole_chiave": ["campata", "statale chiusa", "fascicolo"], "fonti": [1, 2, 3]},
                {"etichetta": "Burocrazia che blocca", "cornice": "I lavori c'erano, li hanno fermati vincoli e controlli.", "parole_chiave": ["burocrati", "vincoli", "Soprintendenza"], "fonti": [7, 8]},
            ],
            "omissioni": [
                {"elemento": "L'esistenza della relazione tecnica del 2024 sui piloni", "presente_in": [4, 5, 6], "assente_in": [7, 8]},
                {"elemento": "La versione della Regione sui fondi stanziati", "presente_in": [5, 7], "assente_in": [4, 6]},
            ],
            "linguaggio": [
                {"termine": "strage sfiorata", "fonte": 8, "alternativa_neutra": "crollo con feriti", "perche": "Evoca morti che non ci sono stati."},
                {"termine": "ponte della vergogna", "fonte": 6, "alternativa_neutra": "ponte sul Serra", "perche": "Giudizio morale nel nome stesso dell'oggetto."},
                {"termine": "tragedia annunciata", "fonte": 4, "alternativa_neutra": "crollo segnalato come rischio nel 2024", "perche": "Presuppone una colpa non ancora accertata."},
                {"termine": "i burocrati dormono", "fonte": 8, "alternativa_neutra": "i lavori erano in attesa di autorizzazioni", "perche": "Attribuisce intenzioni."},
            ],
            "domande_aperte": [
                "Quante persone sono rimaste ferite, secondo una fonte ufficiale?",
                "Perché la relazione del 2024 non ha portato a lavori entro i dodici mesi raccomandati?",
                "I 2,1 milioni del 2025 sono stati effettivamente stanziati e su quale capitolo?",
                "Quanto resterà chiusa la statale 14?",
            ],
            "contesto": "Il ponte collega Borgo Alto alla statale 14 ed è l'accesso principale da sud. La relazione del 2024 è citata da tre testate ma non è stata pubblicata integralmente.",
        },
    },
    {
        "hours": 7,
        "articles": [
            ("demo_lince", 9, "Valdora, approvata la legge sugli affitti brevi: tetto di 120 notti",
             "Il Consiglio regionale della Valdora ha approvato con 28 voti favorevoli e 19 contrari la legge sugli affitti brevi. "
             "Nei comuni ad alta tensione abitativa gli alloggi interi potranno essere affittati per un massimo di 120 notti l'anno. "
             "La legge entrerà in vigore a marzo."),
            ("demo_faro", 8, "Affitti brevi, finalmente un argine: le case tornano ai residenti",
             "Con il tetto di 120 notti la Valdora prova a restituire le case a chi ci vive. Nei centri storici, secondo l'osservatorio "
             "regionale, un alloggio su quattro è su piattaforme di affitto breve. Una legge attesa da anni."),
            ("demo_pendolo", 7.5, "Affitti brevi, la Regione fissa il limite a 120 notti",
             "Approvata con 28 voti a favore e 19 contrari la legge regionale sugli affitti brevi. Il limite di 120 notti vale solo nei "
             "comuni ad alta tensione abitativa, che la giunta individuerà entro gennaio. Contrari i gruppi di opposizione e le associazioni dei proprietari."),
            ("demo_baluardo", 6, "Esproprio mascherato: la Regione mette le mani sulle case dei proprietari",
             "La nuova legge è un esproprio mascherato della proprietà privata. Le associazioni dei proprietari annunciano ricorso "
             "e stimano una perdita di 300 milioni di euro di indotto turistico. Il tetto di 120 notti colpirà le famiglie che "
             "arrotondano con un appartamento."),
            ("demo_megafono", 5, "Affitti brevi, la sinistra fa la guerra ai piccoli proprietari",
             "Ennesima stangata: 120 notti e poi basta. Secondo le associazioni dei proprietari andranno persi 300 milioni di indotto. "
             "La legge è passata con i voti della maggioranza."),
        ],
        "llm": {
            "titolo_neutro": "La Valdora approva il tetto di 120 notti l'anno per gli affitti brevi",
            "sezione": "Politica",
            "sommario": "Il Consiglio regionale ha approvato con 28 voti a favore e 19 contrari una legge che limita a 120 notti l'anno l'affitto breve di alloggi interi nei comuni ad alta tensione abitativa.",
            "fatti": [
                {"testo": "La legge è stata approvata con 28 voti favorevoli e 19 contrari.", "stato": "confermato", "fonti": [1, 3]},
                {"testo": "Il tetto è di 120 notti l'anno per gli alloggi interi.", "stato": "confermato", "fonti": [1, 2, 3, 4, 5]},
                {"testo": "Il limite vale solo nei comuni ad alta tensione abitativa, ancora da individuare.", "stato": "confermato", "fonti": [1, 3]},
                {"testo": "Un alloggio su quattro nei centri storici è su piattaforme di affitto breve.", "stato": "riportato", "fonti": [2], "nota": "Dato attribuito all'osservatorio regionale, non pubblicato."},
                {"testo": "La legge causerà una perdita di 300 milioni di euro di indotto.", "stato": "non_verificato", "fonti": [4, 5], "nota": "Stima delle associazioni dei proprietari, metodo non indicato."},
            ],
            "interpretazioni": [
                {"testo": "La legge restituisce le case ai residenti.", "tipo": "previsione", "fonti": [2]},
                {"testo": "La legge è un esproprio della proprietà privata.", "tipo": "giudizio", "fonti": [4, 5]},
            ],
            "divergenze": [
                {"tema": "Chi colpisce la legge", "versioni": [
                    {"racconto": "Le piattaforme e la concentrazione di alloggi nei centri storici.", "fonti": [2]},
                    {"racconto": "Le famiglie con un solo appartamento in affitto.", "fonti": [4, 5]},
                ]},
            ],
            "inquadramenti": [
                {"etichetta": "Diritto all'abitare", "cornice": "Una misura per riportare residenti nei centri.", "parole_chiave": ["argine", "residenti"], "fonti": [2]},
                {"etichetta": "Attacco alla proprietà", "cornice": "Una limitazione ingiusta per i piccoli proprietari.", "parole_chiave": ["esproprio", "stangata", "guerra"], "fonti": [4, 5]},
            ],
            "omissioni": [
                {"elemento": "Che il tetto vale solo nei comuni ad alta tensione abitativa", "presente_in": [1, 3], "assente_in": [4, 5, 2]},
            ],
            "linguaggio": [
                {"termine": "esproprio mascherato", "fonte": 4, "alternativa_neutra": "limite all'affitto breve", "perche": "Nessun bene viene espropriato."},
                {"termine": "stangata", "fonte": 5, "alternativa_neutra": "nuovo limite", "perche": "Non è una tassa."},
            ],
            "domande_aperte": ["Quali comuni rientreranno tra quelli ad alta tensione abitativa?", "Su quali dati si basa la stima dei 300 milioni?"],
            "contesto": "",
        },
    },
    {
        "hours": 11,
        "articles": [
            ("demo_lince", 13, "Sciopero dei trasporti locali in Valdora, disagi a Borgo Alto",
             "Sciopero di 24 ore del trasporto pubblico locale in Valdora. Secondo i sindacati l'adesione è stata dell'80 per cento; "
             "secondo l'azienda regionale dei trasporti del 35 per cento. Garantite le fasce 6-9 e 18-21."),
            ("demo_cronache", 12, "Sciopero, adesione all'80%: i lavoratori fermano la Valdora",
             "Adesione all'80 per cento secondo i sindacati. Autisti in piazza contro turni di dieci ore e stipendi fermi da quattro anni."),
            ("demo_vetro", 11.5, "Sciopero dei bus, l'azienda: adesione al 35 per cento",
             "Per l'azienda regionale ha aderito il 35 per cento del personale. I sindacati parlano di 80 per cento. Il contratto è scaduto dal 2022."),
            ("demo_megafono", 10, "Ennesimo venerdì nero: pendolari ostaggio dei sindacati",
             "Pendolari ostaggio dell'ennesimo sciopero. Secondo l'azienda ha aderito solo un terzo dei lavoratori."),
        ],
        "llm": {
            "titolo_neutro": "Sciopero di 24 ore del trasporto locale in Valdora, adesione contestata",
            "sezione": "Economia",
            "sommario": "Sciopero di 24 ore del trasporto pubblico locale in Valdora, con fasce di garanzia 6-9 e 18-21. Sindacati e azienda danno numeri di adesione molto diversi.",
            "fatti": [
                {"testo": "Sciopero di 24 ore del trasporto pubblico locale con fasce garantite 6-9 e 18-21.", "stato": "confermato", "fonti": [1, 3]},
                {"testo": "Percentuale di adesione allo sciopero.", "stato": "contestato", "fonti": [1, 2, 3, 4], "nota": "80% per i sindacati, 35% per l'azienda."},
                {"testo": "Il contratto nazionale è scaduto dal 2022.", "stato": "riportato", "fonti": [3]},
            ],
            "interpretazioni": [
                {"testo": "I pendolari sono ostaggio dei sindacati.", "tipo": "giudizio", "fonti": [4]},
                {"testo": "I lavoratori protestano per condizioni di lavoro insostenibili.", "tipo": "causa", "fonti": [2]},
            ],
            "divergenze": [{"tema": "Adesione", "versioni": [
                {"racconto": "80 per cento (sindacati).", "fonti": [2]},
                {"racconto": "35 per cento (azienda).", "fonti": [3, 4]},
            ]}],
            "inquadramenti": [
                {"etichetta": "Vertenza di lavoro", "cornice": "Lo sciopero come risposta a turni e salari.", "parole_chiave": ["turni", "stipendi fermi"], "fonti": [2]},
                {"etichetta": "Disagio per i cittadini", "cornice": "Lo sciopero come danno ai pendolari.", "parole_chiave": ["ostaggio", "venerdì nero"], "fonti": [4]},
            ],
            "omissioni": [{"elemento": "Le ragioni della protesta (turni, contratto scaduto)", "presente_in": [2, 3], "assente_in": [4]}],
            "linguaggio": [{"termine": "ostaggio dei sindacati", "fonte": 4, "alternativa_neutra": "colpiti dallo sciopero", "perche": "Metafora criminale."}],
            "domande_aperte": ["Esiste un dato di adesione certificato da un ente terzo?"],
            "contesto": "",
        },
    },
    {
        "hours": 20,
        "articles": [
            ("demo_cronache", 22, "Campi della Valdora, un bracciante su tre senza contratto",
             "Secondo il rapporto dell'associazione Terra Giusta, un lavoratore agricolo su tre nella piana della Valdora lavora senza contratto. "
             "Il rapporto si basa su 640 interviste raccolte tra maggio e settembre."),
            ("demo_faro", 21, "Lavoro nero nei campi, il rapporto di Terra Giusta",
             "Un bracciante su tre senza contratto: è la stima del rapporto annuale di Terra Giusta, basato su 640 interviste. "
             "L'ispettorato del lavoro non ha ancora commentato."),
            ("demo_pendolo", 19, "Agricoltura, Terra Giusta: un terzo dei braccianti senza contratto",
             "Il rapporto di Terra Giusta stima che un terzo dei lavoratori agricoli della piana sia senza contratto. Le associazioni "
             "agricole contestano il metodo: 640 interviste non sarebbero un campione rappresentativo."),
        ],
        "llm": {
            "titolo_neutro": "Un rapporto stima un bracciante su tre senza contratto nella piana della Valdora",
            "sezione": "Società",
            "sommario": "Il rapporto annuale dell'associazione Terra Giusta, basato su 640 interviste, stima che un lavoratore agricolo su tre nella piana della Valdora sia senza contratto.",
            "fatti": [
                {"testo": "Il rapporto di Terra Giusta si basa su 640 interviste raccolte tra maggio e settembre.", "stato": "confermato", "fonti": [1, 2, 3]},
                {"testo": "Un lavoratore agricolo su tre nella piana sarebbe senza contratto.", "stato": "riportato", "fonti": [1, 2, 3], "nota": "Stima di un unico rapporto, contestata nel metodo."},
            ],
            "interpretazioni": [{"testo": "640 interviste non sono un campione rappresentativo.", "tipo": "opinione", "fonti": [3]}],
            "divergenze": [],
            "inquadramenti": [],
            "omissioni": [{"elemento": "Le critiche al metodo del rapporto", "presente_in": [3], "assente_in": [1, 2]}],
            "linguaggio": [],
            "domande_aperte": ["Esistono dati dell'ispettorato del lavoro per confronto?"],
            "contesto": "",
        },
    },
    {
        "hours": 16,
        "articles": [
            ("demo_baluardo", 18, "Stazioni insicure: furti in aumento del 40%",
             "Secondo i dati della prefettura di Valdora i furti denunciati nelle stazioni ferroviarie sono aumentati del 40 per cento nei primi nove mesi dell'anno."),
            ("demo_megafono", 17, "Stazioni in mano alle bande: +40% di furti",
             "Furti alle stelle nelle stazioni: +40 per cento. Le bande agiscono indisturbate e i cittadini hanno paura."),
            ("demo_vetro", 15, "Furti nelle stazioni, i dati della prefettura",
             "I furti denunciati nelle stazioni della Valdora sono passati da 210 a 294 nei primi nove mesi dell'anno, secondo la prefettura. "
             "In valore assoluto restano sotto il livello del 2019."),
        ],
        "llm": {
            "titolo_neutro": "Prefettura di Valdora: furti denunciati nelle stazioni da 210 a 294 in nove mesi",
            "sezione": "Cronaca",
            "sommario": "Secondo la prefettura i furti denunciati nelle stazioni ferroviarie della Valdora sono passati da 210 a 294 nei primi nove mesi dell'anno.",
            "fatti": [
                {"testo": "I furti denunciati nelle stazioni sono aumentati del 40 per cento nei primi nove mesi.", "stato": "confermato", "fonti": [1, 2, 3]},
                {"testo": "In valori assoluti: da 210 a 294.", "stato": "riportato", "fonti": [3]},
                {"testo": "I valori restano sotto il livello del 2019.", "stato": "riportato", "fonti": [3]},
            ],
            "interpretazioni": [{"testo": "Le stazioni sono in mano alle bande.", "tipo": "giudizio", "fonti": [2]}],
            "divergenze": [],
            "inquadramenti": [{"etichetta": "Emergenza sicurezza", "cornice": "L'aumento come segno di perdita di controllo.", "parole_chiave": ["bande", "paura", "alle stelle"], "fonti": [1, 2]}],
            "omissioni": [{"elemento": "I valori assoluti e il confronto con il 2019", "presente_in": [3], "assente_in": [1, 2]}],
            "linguaggio": [{"termine": "in mano alle bande", "fonte": 2, "alternativa_neutra": "con più furti denunciati", "perche": "Nessuna fonte parla di bande organizzate."}],
            "domande_aperte": ["L'aumento riguarda i furti o le denunce (es. per nuove modalità di denuncia)?"],
            "contesto": "",
        },
    },
    {
        "hours": 26,
        "articles": [
            ("demo_lince", 28, "Batterie, la valdorese Ionica raccoglie 40 milioni",
             "La startup Ionica, con sede a Borgo Alto, ha chiuso un round da 40 milioni di euro guidato da un fondo europeo. "
             "Servirà ad aprire il primo impianto pilota per batterie al sodio entro il 2028."),
            ("demo_faro", 27, "Ionica, 40 milioni per le batterie al sodio made in Valdora",
             "Quaranta milioni per costruire batterie senza litio: Ionica apre un impianto pilota a Borgo Alto entro il 2028 e prevede 150 assunzioni."),
            ("demo_baluardo", 26, "Ionica, l'eccellenza valdorese che attira capitali",
             "Round da 40 milioni per Ionica: l'impianto pilota sorgerà a Borgo Alto entro il 2028."),
            ("demo_tgvalle", 25, "Ionica chiude un round da 40 milioni",
             "Ionica ha raccolto 40 milioni di euro. L'impianto pilota per batterie al sodio aprirà entro il 2028."),
        ],
        "llm": {
            "titolo_neutro": "La startup Ionica raccoglie 40 milioni per un impianto di batterie al sodio",
            "sezione": "Economia",
            "sommario": "Ionica, startup di Borgo Alto, ha raccolto 40 milioni di euro per aprire entro il 2028 un impianto pilota di batterie al sodio.",
            "fatti": [
                {"testo": "Ionica ha chiuso un round da 40 milioni di euro.", "stato": "confermato", "fonti": [1, 2, 3, 4]},
                {"testo": "L'impianto pilota aprirà a Borgo Alto entro il 2028.", "stato": "confermato", "fonti": [1, 2, 3]},
                {"testo": "Sono previste 150 assunzioni.", "stato": "riportato", "fonti": [2]},
            ],
            "interpretazioni": [],
            "divergenze": [],
            "inquadramenti": [],
            "omissioni": [],
            "linguaggio": [],
            "domande_aperte": ["Chi sono gli investitori oltre al fondo capofila?"],
            "contesto": "",
        },
    },
]


STORIES.append({
    "hours": 5,
    "articles": [
        ("demo_lince", 6, "Mare di Corvara, il Parlamento approva la partecipazione alla missione navale",
         "La Camera ha approvato con 312 voti favorevoli e 98 contrari la partecipazione alla missione navale europea nel mare di Corvara. "
         "L'Italia metterà a disposizione due fregate e circa 400 militari per sei mesi. Il costo stimato è di 92 milioni di euro."),
        ("demo_cronache", 5.5, "Missione a Corvara, l'Italia entra in un conflitto che non è suo",
         "Due fregate e 400 militari nel mare di Corvara: il Parlamento dice sì a una missione dai contorni incerti. "
         "Le associazioni pacifiste chiedono di conoscere le regole d'ingaggio, che il governo non ha reso pubbliche."),
        ("demo_pendolo", 5, "Corvara, via libera alla missione: due fregate per sei mesi",
         "Via libera della Camera alla missione navale europea nel mare di Corvara, con 312 sì e 98 no. Due fregate, circa 400 militari, "
         "costo stimato 92 milioni. Le regole d'ingaggio saranno illustrate alle commissioni in seduta riservata."),
        ("demo_vetro", 4.5, "Corvara, l'Italia guida la flotta europea",
         "Secondo fonti della Difesa, all'Italia potrebbe essere affidato il comando della missione navale europea nel mare di Corvara. "
         "La decisione spetta al Consiglio europeo."),
        ("demo_baluardo", 4, "Corvara, finalmente l'Italia torna protagonista nel Mediterraneo",
         "Con due fregate e 400 uomini l'Italia torna a contare. Secondo fonti della Difesa al nostro Paese andrà il comando della missione."),
    ],
    "llm": {
        "titolo_neutro": "La Camera approva la partecipazione italiana alla missione navale nel mare di Corvara",
        "sezione": "Esteri",
        "sommario": "Con 312 voti favorevoli e 98 contrari la Camera ha approvato la partecipazione alla missione navale europea nel mare di Corvara: due fregate e circa 400 militari per sei mesi.",
        "fatti": [
            {"testo": "La Camera ha approvato la partecipazione con 312 voti favorevoli e 98 contrari.", "stato": "confermato", "fonti": [1, 3]},
            {"testo": "L'Italia impiega due fregate e circa 400 militari per sei mesi.", "stato": "confermato", "fonti": [1, 2, 3, 5]},
            {"testo": "Il costo stimato è di 92 milioni di euro.", "stato": "riportato", "fonti": [1, 3], "nota": "Stima riportata dall'agenzia e ripresa."},
            {"testo": "All'Italia andrà il comando della missione.", "stato": "non_verificato", "fonti": [4, 5], "nota": "'Fonti della Difesa'; la decisione spetta al Consiglio europeo."},
            {"testo": "Le regole d'ingaggio non sono state rese pubbliche.", "stato": "confermato", "fonti": [2, 3]},
        ],
        "interpretazioni": [
            {"testo": "La missione coinvolge l'Italia in un conflitto che non la riguarda.", "tipo": "giudizio", "fonti": [2]},
            {"testo": "La missione restituisce all'Italia un ruolo da protagonista.", "tipo": "giudizio", "fonti": [5]},
        ],
        "divergenze": [{"tema": "Chi comanderà la missione", "versioni": [
            {"racconto": "L'Italia, secondo fonti della Difesa.", "fonti": [4, 5]},
            {"racconto": "Non ancora deciso: spetta al Consiglio europeo.", "fonti": [4]},
        ]}],
        "inquadramenti": [
            {"etichetta": "Rischio di guerra", "cornice": "Una missione opaca che espone il Paese.", "parole_chiave": ["conflitto", "contorni incerti"], "fonti": [2]},
            {"etichetta": "Atto parlamentare", "cornice": "Voti, mezzi, costi e tempi della missione.", "parole_chiave": ["via libera", "fregate", "costo"], "fonti": [1, 3]},
            {"etichetta": "Prestigio nazionale", "cornice": "L'Italia torna a contare nel Mediterraneo.", "parole_chiave": ["protagonista", "comando"], "fonti": [4, 5]},
        ],
        "omissioni": [{"elemento": "Le regole d'ingaggio non sono pubbliche", "presente_in": [2, 3], "assente_in": [4, 5]}],
        "linguaggio": [{"termine": "finalmente torna protagonista", "fonte": 5, "alternativa_neutra": "partecipa alla missione", "perche": "Giudizio di valore nel titolo."}],
        "domande_aperte": ["Quali sono le regole d'ingaggio?", "Chi avra' il comando operativo?"],
        "contesto": "",
    },
})


DEMO_UPDATES = {
    1: [
        ("apertura", 4.2, "Prima notizia da Agenzia Lince.", None, None, None),
        ("nuove_testate", 3.1, "Ne parlano anche: Il Faro, Corriere di Vetro.", None, None, None),
        ("cambio_stato", 2.5, "«Una relazione tecnica del 2024 raccomandava interventi sui piloni» passa da non verificato a riportato.",
         "Una relazione tecnica del 2024 raccomandava interventi sui piloni entro dodici mesi.", "non_verificato", "riportato"),
        ("nuove_testate", 1.5, "Ne parlano anche: Il Baluardo, Il Megafono.", None, None, None),
        ("cambio_stato", 1.4, "«Numero dei feriti» passa da confermato a contestato.", "Numero dei feriti.", "confermato", "contestato"),
    ],
}


def _make_article(source_id: str, hours_ago: float, title: str, body: str, now: datetime) -> Article:
    src = get_source(source_id)
    return Article(
        id=hashlib.md5(f"{source_id}:{title}".encode()).hexdigest(),
        source_id=source_id,
        source_name=src.name,
        bias=src.leaning,
        bias_source=src.leaning,
        orientation_score=src.orientation,
        title=title,
        snippet=body[:220] + ("…" if len(body) > 220 else ""),
        body=body,
        url=None,
        published_at=now - timedelta(hours=hours_ago),
    )


def build_demo_edition() -> Edition:
    register_sources(DEMO_SOURCES)
    now = datetime.utcnow()
    stories: List[Story] = []
    for i, spec in enumerate(STORIES):
        arts = [_make_article(sid, h, t, b, now) for sid, h, t, b in spec["articles"]]
        detect_echoes(arts)
        story = Story(
            id=f"demo-{i + 1}",
            query="",
            title=arts[0].title,
            articles=arts,
            stats=_compute_stats(arts),
        )
        # Il dossier usa la numerazione dell'ordine originale degli articoli
        story.dossier = parse_dossier(spec["llm"], arts, {a.id: a for a in arts})
        story.dossier.generated_by = "demo"
        for kind, h, text, fact, fr, to in DEMO_UPDATES.get(i + 1, []):
            story.updates.append(StoryUpdate(at=now - timedelta(hours=h), kind=kind, text=text, fact_text=fact, from_status=fr, to_status=to))
        finalize_story(story, with_dossier=False)
        STORY_CACHE[story.id] = story
        stories.append(story)
    stories.sort(key=lambda s: s.score, reverse=True)
    return assemble_edition(stories, demo=True, sources_ok=len(DEMO_SOURCES), sources_total=len(DEMO_SOURCES))
