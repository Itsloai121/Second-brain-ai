import unittest
from app.calculations import available,average_daily_demand,safety_stock,reorder_point,eoq,days_of_cover
from app.forecasting import forecast_daily
from datetime import date,timedelta
class TestSupplyChain(unittest.TestCase):
 def test_inventory_math(self):
  self.assertEqual(available(100,25),75);self.assertEqual(average_daily_demand([10,20,30]),20);self.assertEqual(days_of_cover(100,10),10)
 def test_planning(self):
  units=[8,10,12,9,11]*12;self.assertGreater(safety_stock(units,30),0);self.assertGreater(reorder_point(units,30),300);self.assertGreater(eoq(5000,100,10),0)
 def test_forecast(self):
  h=[{'date':date.today()-timedelta(days=60-i),'units':10+i%7} for i in range(60)];f=forecast_daily(h,14);self.assertEqual(len(f['daily']),14);self.assertGreater(f['total'],0)
if __name__=='__main__':unittest.main()
