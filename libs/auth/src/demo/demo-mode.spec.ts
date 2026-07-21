import { configure_demo_mode, is_demo_mode } from './demo-mode';

const STORAGE_KEY = 'tc_demo';

/** Mirrors what main.ts does for each build configuration. */
const PROD = { demo: false, allowOverride: false };
const DEMO = { demo: true, allowOverride: true };
const DEV = { demo: false, allowOverride: true };

function setSearch(search: string): void {
  window.history.replaceState({}, '', `/${search}`);
}

describe('is_demo_mode', () => {
  beforeEach(() => {
    window.localStorage.clear();
    setSearch('');
  });

  afterEach(() => {
    window.localStorage.clear();
    setSearch('');
  });

  describe('production build (locked)', () => {
    beforeEach(() => configure_demo_mode(PROD.demo, PROD.allowOverride));

    it('is off by default', () => {
      expect(is_demo_mode()).toBe(false);
    });

    // The original bug: build_default was hardcoded true and configure_demo_mode
    // was never called, so production served canned data.
    it('stays off when ?demo=1 is in the URL', () => {
      setSearch('?demo=1');
      expect(is_demo_mode()).toBe(false);
    });

    // A prospect's browser keeps localStorage after a sales demo. Production
    // must not honour that flag.
    it('stays off with a stale localStorage flag', () => {
      window.localStorage.setItem(STORAGE_KEY, '1');
      expect(is_demo_mode()).toBe(false);
    });

    it('stays off with both a stale flag and ?demo=1', () => {
      window.localStorage.setItem(STORAGE_KEY, '1');
      setSearch('?demo=1');
      expect(is_demo_mode()).toBe(false);
    });

    it('does not write to localStorage when a query param is present', () => {
      setSearch('?demo=1');
      is_demo_mode();
      expect(window.localStorage.getItem(STORAGE_KEY)).toBeNull();
    });
  });

  describe('demo build', () => {
    beforeEach(() => configure_demo_mode(DEMO.demo, DEMO.allowOverride));

    it('is on by default', () => {
      expect(is_demo_mode()).toBe(true);
    });

    it('can be pointed at a real backend with ?demo=0', () => {
      setSearch('?demo=0');
      expect(is_demo_mode()).toBe(false);
    });
  });

  describe('development build', () => {
    beforeEach(() => configure_demo_mode(DEV.demo, DEV.allowOverride));

    it('is off by default', () => {
      expect(is_demo_mode()).toBe(false);
    });

    it('honours ?demo=1 and remembers it', () => {
      setSearch('?demo=1');
      expect(is_demo_mode()).toBe(true);
      expect(window.localStorage.getItem(STORAGE_KEY)).toBe('1');
    });

    it('honours a stored flag once the query param is gone', () => {
      window.localStorage.setItem(STORAGE_KEY, '1');
      expect(is_demo_mode()).toBe(true);
    });

    it('lets ?demo=0 clear a stored flag', () => {
      window.localStorage.setItem(STORAGE_KEY, '1');
      setSearch('?demo=0');
      expect(is_demo_mode()).toBe(false);
      expect(window.localStorage.getItem(STORAGE_KEY)).toBe('0');
    });
  });
});
