/* app.js — Alpine.js component for Property Watcher UI */

function propertyWatcher() {
  return {
    // ── tab state ──────────────────────────────────────────────────
    tab: 'listings',

    // ── run status ────────────────────────────────────────────────
    running: false,
    lastRunAt: null,
    lastRunNewCount: 0,
    lastRunError: null,
    runStatusInterval: null,

    // ── listings tab ──────────────────────────────────────────────
    listings: [],
    listingsTotal: 0,
    listingsPage: 1,
    listingsLimit: 20,
    listingsLoading: false,
    listingsSource: '',

    // ── keywords tab ─────────────────────────────────────────────
    cfg: {
      locations: [],
      property_types: [],
      must_keywords: [],
      reject_keywords: [],
      max_price_inr: 0,
      enabled_scrapers: [],
    },
    cfgLoading: false,
    cfgSaved: false,
    newInputs: {
      locations: '',
      property_types: '',
      must_keywords: '',
      reject_keywords: '',
    },

    // ── sources tab ───────────────────────────────────────────────
    scrapers: [],
    scrapersLoading: false,

    // ── run history (in-memory last 20) ───────────────────────────
    history: [],

    // ── init ──────────────────────────────────────────────────────
    async init() {
      await this.fetchRunStatus();
      await this.fetchListings();
      this.runStatusInterval = setInterval(() => this.fetchRunStatus(), 8000);
    },

    destroy() {
      clearInterval(this.runStatusInterval);
    },

    // ── tab switching ─────────────────────────────────────────────
    async switchTab(t) {
      this.tab = t;
      if (t === 'listings')  await this.fetchListings();
      if (t === 'keywords')  await this.fetchConfig();
      if (t === 'sources')   await this.fetchScrapers();
      if (t === 'history')   {}   // history is accumulated from run-status polls
    },

    // ── run status ────────────────────────────────────────────────
    async fetchRunStatus() {
      try {
        const r = await fetch('/api/run/status');
        const d = await r.json();
        const wasRunning = this.running;
        this.running          = d.running;
        this.lastRunAt        = d.last_run_at;
        this.lastRunNewCount  = d.last_run_new_count;
        this.lastRunError     = d.last_run_error;

        // if a run just finished, refresh listings and log to history
        if (wasRunning && !d.running) {
          this.history.unshift({
            at: d.last_run_at,
            count: d.last_run_new_count,
            error: d.last_run_error,
          });
          if (this.history.length > 20) this.history.pop();
          if (this.tab === 'listings') await this.fetchListings();
        }
      } catch (_) {}
    },

    async triggerRun() {
      if (this.running) return;
      this.running = true;
      try {
        const r = await fetch('/api/run', { method: 'POST' });
        if (!r.ok) {
          const e = await r.json();
          alert(e.detail || 'Could not start run.');
          this.running = false;
        }
      } catch (_) { this.running = false; }
    },

    formatTime(iso) {
      if (!iso) return '—';
      const d = new Date(iso);
      const diff = Math.round((Date.now() - d.getTime()) / 60000);
      if (diff < 1)   return 'just now';
      if (diff < 60)  return `${diff}m ago`;
      if (diff < 1440) return `${Math.round(diff / 60)}h ago`;
      return d.toLocaleDateString();
    },

    // ── listings ──────────────────────────────────────────────────
    async fetchListings() {
      this.listingsLoading = true;
      try {
        const params = new URLSearchParams({
          page: this.listingsPage,
          limit: this.listingsLimit,
          ...(this.listingsSource ? { source: this.listingsSource } : {}),
        });
        const r = await fetch(`/api/listings?${params}`);
        const d = await r.json();
        this.listings      = d.items || [];
        this.listingsTotal = d.total || 0;
      } catch (_) {
        this.listings = [];
      } finally {
        this.listingsLoading = false;
      }
    },

    get totalPages() {
      return Math.max(1, Math.ceil(this.listingsTotal / this.listingsLimit));
    },

    async goPage(p) {
      if (p < 1 || p > this.totalPages) return;
      this.listingsPage = p;
      await this.fetchListings();
    },

    formatPrice(p) {
      if (!p || p === 'N/A') return '—';
      return p;
    },

    // ── config / keywords ─────────────────────────────────────────
    async fetchConfig() {
      this.cfgLoading = true;
      try {
        const r = await fetch('/api/config');
        this.cfg = await r.json();
      } catch (_) {} finally {
        this.cfgLoading = false;
      }
    },

    addTag(field) {
      const val = this.newInputs[field].trim().toLowerCase();
      if (val && !this.cfg[field].includes(val)) {
        this.cfg[field].push(val);
      }
      this.newInputs[field] = '';
    },

    removeTag(field, idx) {
      this.cfg[field].splice(idx, 1);
    },

    handleTagEnter(field, event) {
      if (event.key === 'Enter') { event.preventDefault(); this.addTag(field); }
    },

    async saveConfig() {
      this.cfgSaved = false;
      try {
        await fetch('/api/config', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.cfg),
        });
        this.cfgSaved = true;
        setTimeout(() => { this.cfgSaved = false; }, 3000);
      } catch (_) { alert('Failed to save config.'); }
    },

    // ── scrapers / sources ────────────────────────────────────────
    async fetchScrapers() {
      this.scrapersLoading = true;
      try {
        const r = await fetch('/api/scrapers');
        this.scrapers = await r.json();
      } catch (_) {} finally {
        this.scrapersLoading = false;
      }
    },

    async toggleScraper(scraper) {
      scraper.enabled = !scraper.enabled;
      try {
        await fetch(`/api/scrapers/${scraper.name}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled: scraper.enabled }),
        });
      } catch (_) {
        scraper.enabled = !scraper.enabled; // revert on error
      }
    },

    statusLabel(s) {
      return { active: 'Active', js_only: 'JS-only', blocked: 'Blocked' }[s] || s;
    },
  };
}
