const path = require('path');
const fs = require('fs');

function loadShippingRates() {
  return JSON.parse(
    fs.readFileSync(path.join(__dirname, 'shipping_rates.json'), 'utf8')
  );
}

function loadTaxRules() {
  return JSON.parse(
    fs.readFileSync(path.join(__dirname, 'tax_rules.json'), 'utf8')
  );
}

function registerImportCalculatorRoutes(app) {
  app.get('/import-calculator', (req, res) => {
    const SHIPPING = loadShippingRates();
    const TAX = loadTaxRules();
    res.render('import-calculator', { shippingRates: SHIPPING, taxRules: TAX });
  });

  app.post('/api/calculate-import', (req, res) => {
    const SHIPPING = loadShippingRates();
    const TAX = loadTaxRules();

    const {
      origin_type, country, car_type, car_price_usd,
      exchange_rate, engine_cc, insurance_usd,
      shipping_method = 'container', port = 'Alexandria',
    } = req.body;

    if (!SHIPPING[origin_type]) return res.status(400).json({ error: 'Invalid origin type' });
    if (!SHIPPING[origin_type][country]) return res.status(400).json({ error: 'Country not supported' });
    if (!['electric', 'hybrid', 'fuel'].includes(car_type)) return res.status(400).json({ error: 'Invalid car type' });
    if ((car_type === 'fuel' || car_type === 'hybrid') && !engine_cc) {
      return res.status(400).json({ error: 'Engine CC required for fuel and hybrid vehicles' });
    }

    const baseShipping = SHIPPING[origin_type][country];
    const methodMultiplier = SHIPPING.shipping_methods?.[shipping_method]?.multiplier || 1;
    const portMultiplier = SHIPPING.ports?.[port] || 1;
    const shipping_usd = baseShipping * methodMultiplier * portMultiplier;

    const shippingBreakdown = {
      base_price: baseShipping, method: shipping_method,
      method_multiplier: methodMultiplier, port,
      port_multiplier: portMultiplier, final_shipping: shipping_usd,
    };

    const fixed_port = TAX.fixed_fees_usd?.port_clearance || 600;
    const fixed_broker = TAX.fixed_fees_usd?.customs_broker || 0;
    const insurance = (insurance_usd !== undefined && insurance_usd !== null && insurance_usd !== '') ? parseFloat(insurance_usd) : 200;

    const cif_usd = parseFloat(car_price_usd) + shipping_usd + insurance;
    const cif_egp = cif_usd * parseFloat(exchange_rate);

    let taxes;
    if (car_type === 'electric') {
      taxes = TAX[origin_type].electric;
    } else {
      const cc = parseInt(engine_cc, 10);
      const taxBand = cc <= 1600 ? '1600' : cc <= 1999 ? '1601-1999' : '2000+';
      taxes = TAX[origin_type][car_type][taxBand];
    }

    if (!taxes) return res.status(400).json({ error: 'Could not find tax rates for this configuration' });

    const customs_val = cif_egp * (taxes.customs / 100);
    const dev_val = cif_egp * (taxes.development / 100);
    const table_val = cif_egp * (taxes.table / 100);
    const vat_base = cif_egp + customs_val + dev_val + table_val;
    const vat_val = vat_base * (taxes.vat / 100);

    const total_taxes = customs_val + dev_val + table_val + vat_val;
    const final_cost = cif_egp + total_taxes + fixed_port * parseFloat(exchange_rate);

    res.json({
      disclaimer: TAX.disclaimer || 'Estimates only. Actual costs may vary.',
      costs: {
        car_price_usd: parseFloat(car_price_usd), shipping_usd: Math.round(shipping_usd * 100) / 100,
        insurance_usd: insurance, port_clearance_usd: fixed_port,
        customs_broker_usd: fixed_broker, cif_usd: Math.round(cif_usd * 100) / 100,
        cif_egp: Math.round(cif_egp * 100) / 100,
      },
      shipping: shippingBreakdown,
      taxes: {
        customs: { rate: taxes.customs, value: Math.round(customs_val * 100) / 100 },
        development_fee: { rate: taxes.development, value: Math.round(dev_val * 100) / 100 },
        table_tax: { rate: taxes.table, value: Math.round(table_val * 100) / 100 },
        vat: { rate: taxes.vat, value: Math.round(vat_val * 100) / 100 },
      },
      total_taxes_egp: Math.round(total_taxes * 100) / 100,
      final_import_cost_egp: Math.round(final_cost * 100) / 100,
    });
  });
}

module.exports = {
  registerImportCalculatorRoutes,
};
