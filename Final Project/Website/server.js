const express = require('express');
const path = require('path');
require('dotenv').config({ override: true });
const { registerImportCalculatorRoutes } = require('./Calculator/routes');
const admin = require('firebase-admin');
const pool = require('./db');

// ── Auto-create required tables ──────────────────────────────────────────────
async function initDatabase() {
  try {
    console.log('[DB INIT] Checking / creating required tables...');
    await pool.query(`
      CREATE TABLE IF NOT EXISTS users (
        firebase_uid TEXT PRIMARY KEY,
        email TEXT,
        created_at TIMESTAMP DEFAULT NOW()
      );
      CREATE TABLE IF NOT EXISTS chat_sessions (
        chat_id SERIAL PRIMARY KEY,
        firebase_uid TEXT NOT NULL,
        chat_log JSONB,
        created_at TIMESTAMP DEFAULT NOW()
      );
      CREATE TABLE IF NOT EXISTS favorites (
        id SERIAL PRIMARY KEY,
        firebase_uid TEXT NOT NULL,
        car_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(firebase_uid, car_id)
      );
      CREATE TABLE IF NOT EXISTS saved_comparisons (
        id SERIAL PRIMARY KEY,
        firebase_uid TEXT NOT NULL,
        car_ids TEXT[] NOT NULL,
        comparison_data JSONB,
        created_at TIMESTAMP DEFAULT NOW()
      );
    `);
    console.log('[DB INIT] All tables verified / created successfully.');
  } catch (err) {
    console.error('[DB INIT ERROR] Failed to create tables:', err.message);
    console.error('[DB INIT ERROR] Full error:', err);
  }
}

const serviceAccount = require('./firebase-service-account.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const app = express();

const port = process.env.PORT || process.env.NODE_PORT;
const chatbotApiUrl = process.env.CHATBOT_API_URL;

if (!port) {
  throw new Error("NODE_PORT or PORT is not defined in the environment.");
}
if (!chatbotApiUrl) {
  throw new Error("CHATBOT_API_URL is not defined in the environment.");
}

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ limit: '10mb', extended: true }));

app.get('/', (req, res) => {
  res.render('index');
});

app.get('/new', (req, res) => {
  res.render('cars', { title: 'New Cars', conditionContext: 'new' });
});

app.get('/used', (req, res) => {
  res.render('cars', { title: 'Used Cars', conditionContext: 'used' });
});

app.get('/car/:id', (req, res) => {
  res.render('car', { carId: req.params.id });
});

app.get('/compare', (req, res) => {
  res.render('compare');
});

app.get('/view-chat', (req, res) => {
  res.render('index', { title: 'View History', conditionContext: '', viewOnly: true });
});

app.get('/profile', (req, res) => {
  res.render('profile');
});

app.get('/auth', (req, res) => {
  res.render('auth');
});

app.get('/forgot-password', (req, res) => {
  res.render('forgot-password');
});

app.post('/api/auth/sync-user', async (req, res) => {
  console.log('[SYNC-USER] ▶ Route hit — /api/auth/sync-user');
  try {
    const { idToken } = req.body;
    if (!idToken) {
      console.error('[SYNC-USER] ✖ No idToken in request body');
      return res.status(401).json({ error: 'No token provided' });
    }
    console.log('[SYNC-USER] ✓ idToken received (length:', idToken.length, ')');

    const decodedToken = await admin.auth().verifyIdToken(idToken);
    const uid = decodedToken.uid;
    const email = decodedToken.email;
    console.log(`[SYNC-USER] ✓ Token verified — UID=${uid}, Email=${email}`);

    // Test DB connection first
    try {
      const connTest = await pool.query('SELECT NOW()');
      console.log('[SYNC-USER] ✓ DB connection alive — server time:', connTest.rows[0].now);
    } catch (dbConnErr) {
      console.error('[SYNC-USER] ✖ DB CONNECTION FAILED:', dbConnErr.message);
      console.error('[SYNC-USER] ✖ Connection string used:', process.env.DATABASE_URL ? '***set***' : '***MISSING***');
      return res.status(500).json({ error: 'Database connection failed' });
    }

    // Insert user
    try {
      const query = `INSERT INTO users (firebase_uid, email) VALUES ($1, $2) ON CONFLICT (firebase_uid) DO UPDATE SET email = $2`;
      const result = await pool.query(query, [uid, email]);
      console.log('[SYNC-USER] ✓ INSERT succeeded — rowCount:', result.rowCount);
    } catch (sqlErr) {
      console.error('[SYNC-USER] ✖ SQL INSERT FAILED:', sqlErr.message);
      console.error('[SYNC-USER] ✖ SQL Error Code:', sqlErr.code);
      console.error('[SYNC-USER] ✖ SQL Detail:', sqlErr.detail);
      return res.status(500).json({ error: 'Database insert failed' });
    }

    res.status(200).json({ uid, synced: true });
  } catch (error) {
    console.error('[SYNC-USER] ✖ Token verification failed:', error.message);
    console.error('[SYNC-USER] ✖ Full error:', error);
    res.status(401).json({ error: 'Unauthorized' });
  }
});

app.get('/api/options', async (req, res) => {
  try {
    const brand = req.query.brand;
    const brandsRes = await pool.query('SELECT DISTINCT brand FROM cars WHERE brand IS NOT NULL ORDER BY brand');
    
    let modelsRes;
    if (brand) {
      modelsRes = await pool.query('SELECT DISTINCT model FROM cars WHERE model IS NOT NULL AND brand = $1 ORDER BY model', [brand]);
    } else {
      modelsRes = await pool.query('SELECT DISTINCT model FROM cars WHERE model IS NOT NULL ORDER BY model');
    }
    
    const colorsRes = await pool.query('SELECT DISTINCT color FROM cars WHERE color IS NOT NULL ORDER BY color');
    const transRes = await pool.query('SELECT DISTINCT transmission FROM cars WHERE transmission IS NOT NULL ORDER BY transmission');
    const fuelRes = await pool.query('SELECT DISTINCT fuel_type FROM cars WHERE fuel_type IS NOT NULL ORDER BY fuel_type');
    const bodyRes = await pool.query('SELECT DISTINCT body_type FROM cars WHERE body_type IS NOT NULL ORDER BY body_type');
    const driveRes = await pool.query('SELECT DISTINCT drivetrain FROM cars WHERE drivetrain IS NOT NULL ORDER BY drivetrain');
    
    res.json({
      brands: brandsRes.rows.map(r => r.brand),
      models: modelsRes.rows.map(r => r.model),
      colors: colorsRes.rows.map(r => r.color),
      transmissions: transRes.rows.map(r => r.transmission),
      fuelTypes: fuelRes.rows.map(r => r.fuel_type),
      bodyTypes: bodyRes.rows.map(r => r.body_type),
      drivetrains: driveRes.rows.map(r => r.drivetrain)
    });
  } catch(e) {
    console.error(e);
    res.status(500).json({ error: 'Failed to fetch options' });
  }
});

app.get('/api/cars', async (req, res) => {
  try {
    const { 
      condition, detailed_condition, brand, model, minPrice, maxPrice, color, transmission, 
      minYear, maxYear, minMileage, maxMileage, fuel_type, body_type, drivetrain,
      limit = 12, offset = 0 
    } = req.query;

    let params = [];
    let conditions = [];

    if (condition === 'new') {
        conditions.push("(LOWER(condition) LIKE '%new%' OR LOWER(car_condition) LIKE '%new%')");
    } else if (condition === 'used') {
        conditions.push("(LOWER(condition) LIKE '%used%' OR LOWER(car_condition) LIKE '%used%')");
    }

    if (detailed_condition) {
        params.push(detailed_condition.toLowerCase());
        conditions.push(`LOWER(condition) = $${params.length}`);
    }

    if (brand) { params.push(brand); conditions.push(`brand = $${params.length}`); }
    if (model) { params.push(model); conditions.push(`model = $${params.length}`); }
    if (color) { params.push(color); conditions.push(`color = $${params.length}`); }
    if (transmission) { params.push(transmission); conditions.push(`transmission = $${params.length}`); }
    if (fuel_type) { params.push(fuel_type); conditions.push(`fuel_type = $${params.length}`); }
    if (body_type) { params.push(body_type); conditions.push(`body_type = $${params.length}`); }
    if (drivetrain) { params.push(drivetrain); conditions.push(`drivetrain = $${params.length}`); }
    
    if (minPrice) { params.push(minPrice); conditions.push(`price >= $${params.length}`); }
    if (maxPrice) { params.push(maxPrice); conditions.push(`price <= $${params.length}`); }
    
    if (minYear) { params.push(minYear); conditions.push(`year >= $${params.length}`); }
    if (maxYear) { params.push(maxYear); conditions.push(`year <= $${params.length}`); }

    if (minMileage) { params.push(minMileage); conditions.push(`mileage >= $${params.length}`); }
    if (maxMileage) { params.push(maxMileage); conditions.push(`mileage <= $${params.length}`); }

    let whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
    
    params.push(limit);
    let limitIdx = params.length;
    params.push(offset);
    let offsetIdx = params.length;

    const hasUserFilters = brand || model || color || transmission || fuel_type || body_type || drivetrain || minPrice || maxPrice || minYear || maxYear || minMileage || maxMileage;
    const orderByClause = hasUserFilters 
        ? "ORDER BY brand, model, year DESC, price ASC" 
        : "ORDER BY RANDOM()";

    const query = `
      SELECT * FROM cars 
      ${whereClause} 
      ${orderByClause} 
      LIMIT $${limitIdx} OFFSET $${offsetIdx}
    `;

    const result = await pool.query(query, params);
    
    const countQuery = `SELECT COUNT(*) FROM cars ${whereClause}`;
    const countParams = params.slice(0, params.length - 2);
    const countResult = await pool.query(countQuery, countParams);
    
    res.json({
      cars: result.rows,
      totalCount: parseInt(countResult.rows[0].count, 10)
    });

  } catch (error) {
    console.error('Error fetching cars:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

app.get('/api/cars/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const query = `SELECT * FROM cars WHERE car_id = $1;`;
    const { rows } = await pool.query(query, [id]);
    
    if (rows.length === 0) {
      return res.status(404).json({ error: 'Car not found' });
    }
    
    res.json(rows[0]);
  } catch (error) {
    console.error('Error executing query', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

app.post('/api/chat', async (req, res) => {
  const { message } = req.body;
  if (!message) return res.status(400).json({ error: 'Message is required' });

  try {
    const aiResponse = await fetch(chatbotApiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: message })
    });

    if (!aiResponse.ok) {
        throw new Error('Python API responded with status ' + aiResponse.status);
    }

    const data = await aiResponse.json();
    res.json(data);

  } catch (error) {
    console.error('AI Proxy Error:', error.message);
    res.status(500).json({ 
        text: "⚠️ I'm currently offline. Please ensure the Python AI API is running and accessible.", 
        cars: [] 
    });
  }
});

// ── Auth middleware helper ───────────────────────────────────────────────────
async function verifyAuthToken(req) {
  const authHeader = req.headers.authorization;
  let idToken = null;
  if (authHeader && authHeader.startsWith('Bearer ')) {
    idToken = authHeader.split('Bearer ')[1];
  } else if (req.body && req.body.idToken) {
    idToken = req.body.idToken;
  }
  if (!idToken) throw new Error('No token provided');
  const decoded = await admin.auth().verifyIdToken(idToken);
  return decoded;
}

// ── Favorites Routes ─────────────────────────────────────────────────────────
app.post('/api/favorites', async (req, res) => {
  try {
    const decoded = await verifyAuthToken(req);
    const { carId } = req.body;
    if (!carId) return res.status(400).json({ error: 'carId is required' });
    await pool.query(
      'INSERT INTO favorites (firebase_uid, car_id) VALUES ($1, $2) ON CONFLICT (firebase_uid, car_id) DO NOTHING',
      [decoded.uid, String(carId)]
    );
    res.json({ success: true });
  } catch (err) {
    console.error('[FAVORITES] Error adding favorite:', err.message);
    res.status(401).json({ error: err.message });
  }
});

app.delete('/api/favorites/:carId', async (req, res) => {
  try {
    const decoded = await verifyAuthToken(req);
    await pool.query(
      'DELETE FROM favorites WHERE firebase_uid = $1 AND car_id = $2',
      [decoded.uid, String(req.params.carId)]
    );
    res.json({ success: true });
  } catch (err) {
    console.error('[FAVORITES] Error removing favorite:', err.message);
    res.status(401).json({ error: err.message });
  }
});

app.get('/api/favorites', async (req, res) => {
  try {
    const decoded = await verifyAuthToken(req);
    const result = await pool.query(
      `SELECT c.* FROM favorites f JOIN cars c ON f.car_id::text = c.car_id::text
       WHERE f.firebase_uid = $1 ORDER BY f.created_at DESC`,
      [decoded.uid]
    );
    res.json(result.rows);
  } catch (err) {
    console.error('[FAVORITES] Error fetching favorites:', err.message);
    res.status(401).json({ error: err.message });
  }
});

// ── Comparisons Routes ───────────────────────────────────────────────────────
app.post('/api/comparisons', async (req, res) => {
  try {
    const decoded = await verifyAuthToken(req);
    const { carIds, comparisonData } = req.body;
    if (!carIds || !Array.isArray(carIds) || carIds.length < 2) {
      return res.status(400).json({ error: 'At least 2 carIds required' });
    }
    const result = await pool.query(
      'INSERT INTO saved_comparisons (firebase_uid, car_ids, comparison_data) VALUES ($1, $2, $3) RETURNING id',
      [decoded.uid, carIds, JSON.stringify(comparisonData)]
    );
    res.json({ success: true, id: result.rows[0].id });
  } catch (err) {
    console.error('[COMPARISONS] Error saving comparison:', err.message);
    res.status(401).json({ error: err.message });
  }
});

app.get('/api/comparisons', async (req, res) => {
  try {
    const decoded = await verifyAuthToken(req);
    const result = await pool.query(
      'SELECT * FROM saved_comparisons WHERE firebase_uid = $1 ORDER BY created_at DESC',
      [decoded.uid]
    );
    res.json(result.rows);
  } catch (err) {
    console.error('[COMPARISONS] Error fetching comparisons:', err.message);
    res.status(401).json({ error: err.message });
  }
});

app.delete('/api/comparisons/:id', async (req, res) => {
  try {
    const decoded = await verifyAuthToken(req);
    await pool.query(
      'DELETE FROM saved_comparisons WHERE id = $1 AND firebase_uid = $2',
      [req.params.id, decoded.uid]
    );
    res.json({ success: true });
  } catch (err) {
    console.error('[COMPARISONS] Error deleting comparison:', err.message);
    res.status(401).json({ error: err.message });
  }
});

// ── Chat History Route ───────────────────────────────────────────────────────
app.get('/api/chats/me', async (req, res) => {
  try {
    const decoded = await verifyAuthToken(req);
    const result = await pool.query(
      'SELECT chat_id, chat_log, created_at FROM chat_sessions WHERE firebase_uid = $1 ORDER BY created_at DESC',
      [decoded.uid]
    );
    res.json(result.rows);
  } catch (err) {
    console.error('[CHATS] Error fetching user chats:', err.message);
    res.status(401).json({ error: err.message });
  }
});

app.post('/api/chats/save', async (req, res) => {
  try {
    const { idToken, chatLog, chatId } = req.body;
    if (!idToken || !chatLog) {
      return res.status(400).json({ error: 'Missing required fields' });
    }
    
    // Verify user is logged in
    const decodedToken = await admin.auth().verifyIdToken(idToken);
    const uid = decodedToken.uid;
    
    let result;
    if (chatId) {
      const query = `UPDATE chat_sessions SET chat_log = $1 WHERE chat_id = $2 AND firebase_uid = $3 RETURNING chat_id`;
      result = await pool.query(query, [JSON.stringify(chatLog), chatId, uid]);
    } else {
      const query = `INSERT INTO chat_sessions (firebase_uid, chat_log) VALUES ($1, $2) RETURNING chat_id`;
      result = await pool.query(query, [uid, JSON.stringify(chatLog)]);
    }
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Chat not found or unauthorized' });
    }
    res.status(200).json({ success: true, chatId: result.rows[0].chat_id });
  } catch (error) {
    console.error('Error saving chat session:', error);
    res.status(401).json({ error: 'Unauthorized or invalid token' });
  }
});

app.get('/api/chats/community', async (req, res) => {
  try {
    const query = `
      SELECT c.chat_id, c.chat_log, c.created_at, u.email
      FROM chat_sessions c
      JOIN users u ON c.firebase_uid = u.firebase_uid
      ORDER BY c.created_at DESC
      LIMIT 50
    `;
    const result = await pool.query(query);
    
    const formattedChats = result.rows.map(row => {
      let maskedEmail = row.email;
      if (maskedEmail && maskedEmail.includes('@')) {
        const parts = maskedEmail.split('@');
        const username = parts[0];
        const domain = parts[1];
        const visibleLen = Math.max(1, Math.min(3, username.length - 2));
        maskedEmail = username.substring(0, visibleLen) + '***@' + domain;
      }
      return { ...row, email: maskedEmail };
    });
    
    res.json(formattedChats);
  } catch (error) {
    if (error.code === '42P01') {
        return res.json([]); 
    }
    console.error('Error fetching community chats:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

// ── User History Routes (Valuations & Imports) ──────────────────────────────
app.post('/api/valuations/save', async (req, res) => {
  try {
    const decoded = await verifyAuthToken(req);
    const { make, model, year, predicted_price, features } = req.body;
    const query = `
      INSERT INTO valuation_history (firebase_uid, car_make, car_model, car_year, predicted_price, features)
      VALUES ($1, $2, $3, $4, $5, $6) RETURNING id
    `;
    const result = await pool.query(query, [decoded.uid, make, model, year, predicted_price, JSON.stringify(features)]);
    res.json({ success: true, id: result.rows[0].id });
  } catch (err) {
    console.error('[VALUATIONS] Error saving:', err.message);
    res.status(401).json({ error: err.message });
  }
});

app.get('/api/valuations/me', async (req, res) => {
  try {
    const decoded = await verifyAuthToken(req);
    const result = await pool.query(
      'SELECT * FROM valuation_history WHERE firebase_uid = $1 ORDER BY created_at DESC',
      [decoded.uid]
    );
    res.json(result.rows);
  } catch (err) {
    console.error('[VALUATIONS] Error fetching:', err.message);
    res.status(401).json({ error: err.message });
  }
});

app.post('/api/imports/save', async (req, res) => {
  try {
    const decoded = await verifyAuthToken(req);
    const { make, model, engine_cc, base_price, total_cost, tax_breakdown } = req.body;
    const query = `
      INSERT INTO import_history (firebase_uid, car_make, car_model, engine_cc, base_price, total_cost, tax_breakdown)
      VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id
    `;
    const result = await pool.query(query, [decoded.uid, make || 'N/A', model || 'N/A', engine_cc, base_price, total_cost, JSON.stringify(tax_breakdown)]);
    res.json({ success: true, id: result.rows[0].id });
  } catch (err) {
    console.error('[IMPORTS] Error saving:', err.message);
    res.status(401).json({ error: err.message });
  }
});

app.get('/api/imports/me', async (req, res) => {
  try {
    const decoded = await verifyAuthToken(req);
    const result = await pool.query(
      'SELECT * FROM import_history WHERE firebase_uid = $1 ORDER BY created_at DESC',
      [decoded.uid]
    );
    res.json(result.rows);
  } catch (err) {
    console.error('[IMPORTS] Error fetching:', err.message);
    res.status(401).json({ error: err.message });
  }
});

app.get('/valuation', async (req, res) => {
  try {
    const [brandsRes, colorsRes, transRes, fuelRes, bodyRes, driveRes] = await Promise.all([
        pool.query('SELECT DISTINCT brand FROM cars WHERE brand IS NOT NULL ORDER BY brand'),
        pool.query('SELECT DISTINCT color FROM cars WHERE color IS NOT NULL ORDER BY color'),
        pool.query('SELECT DISTINCT transmission FROM cars WHERE transmission IS NOT NULL ORDER BY transmission'),
        pool.query('SELECT DISTINCT fuel_type FROM cars WHERE fuel_type IS NOT NULL ORDER BY fuel_type'),
        pool.query('SELECT DISTINCT body_type FROM cars WHERE body_type IS NOT NULL ORDER BY body_type'),
        pool.query('SELECT DISTINCT drivetrain FROM cars WHERE drivetrain IS NOT NULL ORDER BY drivetrain')
    ]);

    res.render('valuation', { 
      title: 'Car Valuation',
      brands: brandsRes.rows.map(r => r.brand),
      options: {
        colors: colorsRes.rows.map(r => r.color),
        transmissions: transRes.rows.map(r => r.transmission),
        fuel_types: fuelRes.rows.map(r => r.fuel_type),
        body_shapes: bodyRes.rows.map(r => r.body_type),
        drivetrains: driveRes.rows.map(r => r.drivetrain)
      },
      conditions: ['Excellent', 'Very Good', 'Good', 'Fair', 'Poor']
    });
  } catch(e) {
    console.error(e);
    res.status(500).send("Error loading valuation page");
  }
});

app.get('/trends', (req, res) => {
  res.render('trends', { title: 'Market Trends' });
});

app.get('/trends/:brand/:model', (req, res) => {
  const { brand, model } = req.params;
  res.render('trend-detail', { title: `${brand} ${model} - Price Trends`, brand, model });
});

app.get('/api/trends/cars', async (req, res) => {
  try {
    const { brand, model, search, limit = 50, offset = 0 } = req.query;
    let conditions = [];
    let params = [];

    if (search) {
      params.push(`%${search}%`);
      conditions.push(`(LOWER(brand) LIKE LOWER($${params.length}) OR LOWER(model) LIKE LOWER($${params.length}))`);
    }
    if (brand) { params.push(brand); conditions.push(`brand = $${params.length}`); }
    if (model) { params.push(model); conditions.push(`model = $${params.length}`); }

    const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';

    const query = `
      WITH latest AS (
        SELECT DISTINCT ON (brand, model) 
          brand, model, production_years, average_price, min_price, max_price, month_year as latest_date
        FROM price_history
        ${whereClause}
        ORDER BY brand, model, TO_DATE(month_year, 'Mon-YY') DESC
      )
      SELECT * FROM latest
      ORDER BY brand, model DESC
      LIMIT $${params.length + 1} OFFSET $${params.length + 2}
    `;
    params.push(limit, offset);

    const result = await pool.query(query, params);

    const countQuery = `
      SELECT COUNT(DISTINCT (brand, model)) as count
      FROM price_history ${whereClause}
    `;
    const countParams = params.slice(0, params.length - 2);
    const countResult = await pool.query(countQuery, countParams);

    const brandsRes = await pool.query('SELECT DISTINCT brand FROM price_history ORDER BY brand');

    res.json({
      cars: result.rows,
      totalCount: parseInt(countResult.rows[0].count, 10),
      brands: brandsRes.rows.map(r => r.brand)
    });
  } catch(e) {
    if (e.code === '42P01') {
        return res.json({ cars: [], totalCount: 0, brands: [] });
    }
    console.error(e);
    res.status(500).json({ error: 'Failed to fetch trends data', detail: e.message });
  }
});

app.get('/api/trends/models', async (req, res) => {
  try {
    const { brand } = req.query;
    if (!brand) return res.json({ models: [] });
    
    const query = `SELECT DISTINCT model FROM price_history WHERE brand = $1 ORDER BY model`;
    const result = await pool.query(query, [brand]);
    
    res.json({ models: result.rows.map(r => r.model) });
  } catch(e) {
    if (e.code === '42P01') {
        return res.json({ models: [] });
    }
    console.error(e);
    res.status(500).json({ error: 'Failed to fetch trends models data' });
  }
});

app.get('/api/trends/history', async (req, res) => {
  try {
    const { brand, model } = req.query;
    if (!brand || !model) {
      return res.status(400).json({ error: 'brand and model are required' });
    }

    const query = `
      SELECT month_year as date, 
             MAX(production_years) as production_years,
             ROUND(AVG(average_price::numeric)) as average_price, 
             ROUND(MIN(min_price::numeric)) as min_price, 
             ROUND(MAX(max_price::numeric)) as max_price
      FROM price_history
      WHERE brand = $1 AND model = $2
      GROUP BY month_year
      ORDER BY TO_DATE(month_year, 'Mon-YY') ASC
    `;
    const result = await pool.query(query, [brand, model]);

    res.json({ history: result.rows });
  } catch(e) {
    if (e.code === '42P01') {
        return res.json({ history: [] });
    }
    console.error(e);
    res.status(500).json({ error: 'Failed to fetch history data' });
  }
});

app.get('/firebase-config.js', (req, res) => {
  res.type('application/javascript');
  res.send(`
    export const firebaseConfig = {
      apiKey: "${process.env.FIREBASE_API_KEY}",
      authDomain: "${process.env.FIREBASE_AUTH_DOMAIN}",
      projectId: "${process.env.FIREBASE_PROJECT_ID}",
      storageBucket: "${process.env.FIREBASE_STORAGE_BUCKET}",
      messagingSenderId: "${process.env.FIREBASE_MESSAGING_SENDER_ID}",
      appId: "${process.env.FIREBASE_APP_ID}",
      measurementId: "${process.env.FIREBASE_MEASUREMENT_ID}"
    };
  `);
});

registerImportCalculatorRoutes(app);

// Initialize database tables, then start server
initDatabase().then(() => {
  app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
  });
});