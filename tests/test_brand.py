import unittest
import numpy as np
from src.brand_analysis import prepare,backtest
class BrandTests(unittest.TestCase):
 def test_calendar_and_shared_samples(self):
  p=prepare();r=backtest(p)
  self.assertEqual(r.month.nunique(),8)
  self.assertTrue((r.train_end<r.month).all())
  self.assertTrue((r.feature_month<r.month).all())
  self.assertTrue((r.groupby(['model','month']).size()==6).all())
  self.assertTrue(np.allclose(p.groupby('month').sales_relative.mean().dropna(),0,atol=1e-10))
 def test_future_does_not_change_past(self):
  p=prepare();r=backtest(p);q=p.copy();q.loc[q.month.eq(q.month.max()),'sales_relative']+=1000
  s=backtest(q);np.testing.assert_allclose(r.predicted,s.predicted)
 def test_delay_respects_training_availability(self):
  p=prepare();r=backtest(p);d=backtest(p,2,sorted(r.month.unique()))
  self.assertTrue((d.train_end<=d.feature_month).all())
  self.assertEqual(set(r.month),set(d.month))
if __name__=='__main__':unittest.main()
