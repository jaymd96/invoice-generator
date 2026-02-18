/**
 * IndexedDB storage layer for the Invoice Generator web app.
 * Manages clients, company settings, invoices, and timesheets.
 */

const DB_NAME = 'InvoiceGeneratorDB';
const DB_VERSION = 1;

const STORES = {
  clients: 'clients',
  company: 'company',
  invoices: 'invoices',
  timesheets: 'timesheets',
};

let _db = null;

function openDB() {
  if (_db) return Promise.resolve(_db);

  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);

    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains(STORES.clients)) {
        db.createObjectStore(STORES.clients, { keyPath: 'id', autoIncrement: true });
      }
      if (!db.objectStoreNames.contains(STORES.company)) {
        db.createObjectStore(STORES.company, { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains(STORES.invoices)) {
        const store = db.createObjectStore(STORES.invoices, { keyPath: 'id', autoIncrement: true });
        store.createIndex('date', 'invoice_date');
      }
      if (!db.objectStoreNames.contains(STORES.timesheets)) {
        db.createObjectStore(STORES.timesheets, { keyPath: 'id', autoIncrement: true });
      }
    };

    req.onsuccess = (e) => {
      _db = e.target.result;
      resolve(_db);
    };
    req.onerror = () => reject(req.error);
  });
}

function tx(storeName, mode = 'readonly') {
  return openDB().then((db) => {
    const t = db.transaction(storeName, mode);
    return t.objectStore(storeName);
  });
}

function promisify(req) {
  return new Promise((resolve, reject) => {
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

// ---------------------------------------------------------------------------
// Generic CRUD
// ---------------------------------------------------------------------------

async function getAll(storeName) {
  const store = await tx(storeName);
  return promisify(store.getAll());
}

async function getById(storeName, id) {
  const store = await tx(storeName);
  return promisify(store.get(id));
}

async function put(storeName, record) {
  const store = await tx(storeName, 'readwrite');
  return promisify(store.put(record));
}

async function deleteRecord(storeName, id) {
  const store = await tx(storeName, 'readwrite');
  return promisify(store.delete(id));
}

// ---------------------------------------------------------------------------
// Public API: Clients
// ---------------------------------------------------------------------------

const clients = {
  getAll: () => getAll(STORES.clients),
  get: (id) => getById(STORES.clients, id),
  put: (client) => put(STORES.clients, client),
  delete: (id) => deleteRecord(STORES.clients, Number(id)),
};

// ---------------------------------------------------------------------------
// Public API: Company settings (singleton with id = 'default')
// ---------------------------------------------------------------------------

const company = {
  async get() {
    const record = await getById(STORES.company, 'default');
    return record || {
      id: 'default',
      name: '',
      email: '',
      address: [],
      logo: '',
      company_number: '',
      vat_label: 'VAT',
      vat_number: '',
    };
  },
  save(settings) {
    return put(STORES.company, { ...settings, id: 'default' });
  },
};

// ---------------------------------------------------------------------------
// Public API: Invoices
// ---------------------------------------------------------------------------

const invoices = {
  getAll: () => getAll(STORES.invoices),
  get: (id) => getById(STORES.invoices, id),
  save: (invoice) => put(STORES.invoices, invoice),
  delete: (id) => deleteRecord(STORES.invoices, Number(id)),
};

// ---------------------------------------------------------------------------
// Public API: Timesheets
// ---------------------------------------------------------------------------

const timesheets = {
  getAll: () => getAll(STORES.timesheets),
  get: (id) => getById(STORES.timesheets, id),
  save: (ts) => put(STORES.timesheets, ts),
  delete: (id) => deleteRecord(STORES.timesheets, Number(id)),
};

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------

window.db = { clients, company, invoices, timesheets, openDB };
