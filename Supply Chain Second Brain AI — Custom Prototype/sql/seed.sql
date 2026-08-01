INSERT INTO suppliers(code,name,country,payment_terms,moq) VALUES
('SUP-ALP','Alpine Works','Portugal','30% deposit / Net 30',300),('SUP-SUN','Sunfield Manufacturing','Vietnam','Net 45',500),('SUP-NOR','Northstar Packaging','USA','Net 30',1000);
INSERT INTO products(sku,name,category,unit_cost,selling_price,supplier_id,launch_date) VALUES
('NH-HOME-01','Arc Storage Tray','Home',12.50,39.00,(SELECT id FROM suppliers WHERE code='SUP-ALP'),'2025-02-01'),
('NH-TRVL-02','Fold Travel Organizer','Travel',9.40,32.00,(SELECT id FROM suppliers WHERE code='SUP-SUN'),'2025-05-15'),
('NH-DESK-03','Contour Desk Caddy','Office',7.20,28.00,(SELECT id FROM suppliers WHERE code='SUP-ALP'),'2025-09-01');
INSERT INTO inventory(product_id,on_hand,allocated,in_transit) SELECT id, CASE sku WHEN 'NH-HOME-01' THEN 420 WHEN 'NH-TRVL-02' THEN 190 ELSE 610 END, CASE sku WHEN 'NH-HOME-01' THEN 65 WHEN 'NH-TRVL-02' THEN 80 ELSE 30 END, CASE sku WHEN 'NH-TRVL-02' THEN 500 ELSE 0 END FROM products;
INSERT INTO supplier_metrics(supplier_id,measured_on,quoted_lead_days,actual_lead_days,on_time,defect_rate)
SELECT id,current_date-30,CASE code WHEN 'SUP-SUN' THEN 55 ELSE 32 END,CASE code WHEN 'SUP-SUN' THEN 68 ELSE 36 END,code<>'SUP-SUN',CASE code WHEN 'SUP-SUN' THEN .024 ELSE .008 END FROM suppliers;
INSERT INTO sales_daily(product_id,sales_date,channel,units,revenue)
SELECT p.id, d::date, c.channel, GREATEST(0,(CASE p.sku WHEN 'NH-HOME-01' THEN 15 WHEN 'NH-TRVL-02' THEN 12 ELSE 8 END + (extract(doy from d)::int % 7) + CASE c.channel WHEN 'dtc' THEN 5 WHEN 'marketplace' THEN 2 ELSE 0 END)), 0
FROM products p CROSS JOIN generate_series(current_date-119,current_date,'1 day') d CROSS JOIN (VALUES('dtc'),('marketplace'),('wholesale')) c(channel);
UPDATE sales_daily s SET revenue=s.units*p.selling_price FROM products p WHERE s.product_id=p.id;
INSERT INTO knowledge_docs(title,body,source,tags) VALUES
('Purchase approval policy','Purchase orders above $25,000 require Finance approval. Orders above $75,000 also require COO approval. No PO may be sent from an AI-generated draft without human approval.','Policy',ARRAY['purchasing','approval']),
('Seasonal launch playbook','Freeze launch demand plan 12 weeks before launch. Place long-lead components 16 weeks before launch and packaging 10 weeks before launch. Hold a 15 percent launch buffer for hero SKUs.','Operations',ARRAY['launch','forecast']),
('Sunfield supplier note','Sunfield has recently averaged 68 days actual lead time against 55 quoted days. Use actual variability in safety-stock calculations and request milestone updates weekly.','Supplier review',ARRAY['supplier','lead-time']);
