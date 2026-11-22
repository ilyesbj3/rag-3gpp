// Settings + chat history, mirrored in localStorage (wrapped in try/catch: storage may be
// unavailable in private windows or blocked by policy).
const SETTINGS_KEY = "rag3gpp.settings.v1";
const HISTORY_KEY = "rag3gpp.history.v1";
const MAX_HISTORY = 30;

export const DEFAULT_SETTINGS = {
  use_hybrid: true,
  use_reranker: true,
  use_routing: true,
  final_top_k: 6,
  provider: "auto",
};

function read(key) {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function write(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* storage unavailable: keep in memory only */
  }
}

export const state = {
  settings: { ...DEFAULT_SETTINGS, ...(read(SETTINGS_KEY) || {}) },
  history: Array.isArray(read(HISTORY_KEY)) ? read(HISTORY_KEY) : [],
  health: null,
  selectedId: null,
  busy: false,
  lastProvider: null,
};

export function saveSettings() {
  write(SETTINGS_KEY, state.settings);
}

export function pushMessage(msg) {
  state.history.push(msg);
  if (state.history.length > MAX_HISTORY) {
    state.history = state.history.slice(-MAX_HISTORY);
  }
  write(HISTORY_KEY, state.history);
}

export function persistHistory() {
  write(HISTORY_KEY, state.history);
}

export function clearHistory() {
  state.history = [];
  state.selectedId = null;
  write(HISTORY_KEY, state.history);
}
