import Reveal from './assets/reveal/reveal.esm.js';
import RevealNotes from './assets/reveal/plugin/notes/notes.esm.js';

const qaStyles = document.createElement('link');
qaStyles.rel = 'stylesheet';
qaStyles.href = 'qa.css';
document.head.append(qaStyles);

const deck = new Reveal({
  width: 1600,
  height: 900,
  margin: 0.025,
  minScale: 0.5,
  maxScale: 1.5,
  hash: true,
  slideNumber: 'c/t',
  controls: true,
  progress: true,
  center: false,
  transition: 'fade',
  backgroundTransition: 'fade',
  pdfSeparateFragments: false,
  plugins: [RevealNotes]
});

deck.initialize();
