/* Busto de Marco Aurelio — placeholder SVG (§A.2). El emperador filósofo: las
 * Meditaciones = notas a uno mismo = el Códice. Cerámica/mármol con veta bronce.
 * Cuando David tenga el logo real, se cambia por <img src="…"> en el mismo hueco
 * (ver el marcador data-au-logo en index.html). NO es el logo de Hexelion. */

export const BUST_SVG = `
<svg viewBox="0 0 120 140" role="img" aria-label="Aurelius — bust of the philosopher emperor" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="marbre" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#F3ECDD"/>
      <stop offset="0.55" stop-color="#E4D9C2"/>
      <stop offset="1" stop-color="#CBB994"/>
    </linearGradient>
    <linearGradient id="bronze" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#E0B060"/>
      <stop offset="1" stop-color="#9A6A2E"/>
    </linearGradient>
    <radialGradient id="halo" cx="0.5" cy="0.38" r="0.6">
      <stop offset="0" stop-color="#7C5CE0" stop-opacity="0.30"/>
      <stop offset="1" stop-color="#7C5CE0" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <circle cx="60" cy="52" r="52" fill="url(#halo)"/>
  <!-- pedestal -->
  <rect x="34" y="118" width="52" height="14" rx="2" fill="url(#bronze)"/>
  <rect x="30" y="130" width="60" height="6" rx="2" fill="#7A5222"/>
  <!-- shoulders / toga -->
  <path d="M28 118 C30 96 42 90 60 90 C78 90 90 96 92 118 Z" fill="url(#marbre)"/>
  <path d="M60 90 L60 118 M48 96 L44 118 M72 96 L76 118" stroke="#C7B48C" stroke-width="1.4" fill="none" opacity="0.7"/>
  <!-- neck -->
  <rect x="52" y="80" width="16" height="18" rx="6" fill="url(#marbre)"/>
  <!-- head -->
  <ellipse cx="60" cy="58" rx="24" ry="27" fill="url(#marbre)"/>
  <!-- curly hair (Marcus Aurelius) -->
  <g fill="#D8C7A0">
    <circle cx="42" cy="44" r="6"/><circle cx="50" cy="38" r="6.5"/>
    <circle cx="60" cy="35" r="7"/><circle cx="70" cy="38" r="6.5"/>
    <circle cx="78" cy="44" r="6"/><circle cx="40" cy="54" r="5"/><circle cx="80" cy="54" r="5"/>
  </g>
  <!-- brow + eyes (stoic, downcast) -->
  <path d="M50 56 q5 -3 10 0 M62 56 q5 -3 10 0" stroke="#9A895F" stroke-width="1.6" fill="none" stroke-linecap="round"/>
  <circle cx="54" cy="60" r="1.6" fill="#6B5C3B"/><circle cx="68" cy="60" r="1.6" fill="#6B5C3B"/>
  <!-- nose -->
  <path d="M61 61 L58 72 q3 2 6 0" stroke="#B7A377" stroke-width="1.4" fill="none" stroke-linecap="round"/>
  <!-- curly beard -->
  <g fill="#D8C7A0">
    <circle cx="48" cy="76" r="5.5"/><circle cx="56" cy="82" r="6"/>
    <circle cx="64" cy="82" r="6"/><circle cx="72" cy="76" r="5.5"/>
    <circle cx="60" cy="86" r="6.5"/><circle cx="52" cy="80" r="5"/><circle cx="68" cy="80" r="5"/>
  </g>
  <path d="M53 74 q7 6 14 0" stroke="#9A895F" stroke-width="1.4" fill="none" stroke-linecap="round"/>
</svg>`;
