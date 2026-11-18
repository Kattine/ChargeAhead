"""Integrity tests for time leakage, equal comparison windows and source parsing."""
import unittest
import numpy as np
import pandas as pd
from src.analysis import ROOT, prepare_panel, prepare_attention, forecast, summarize


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = prepare_panel()
        cls.a, _ = prepare_attention()
        cls.f = forecast(cls.p, cls.a)

    def test_future_values_do_not_change_earlier_predictions(self):
        cutoff = pd.Timestamp("2025-12-01")
        p, a = self.p.copy(), self.a.copy()
        p.loc[p.month >= cutoff, "nev_share"] = .99
        a.loc[a.month >= cutoff, "attention_change"] = 1e8
        changed = forecast(p,a)
        before = self.f.loc[self.f.month < cutoff,"predicted_change_pp"].to_numpy()
        after = changed.loc[changed.month < cutoff,"predicted_change_pp"].to_numpy()
        np.testing.assert_allclose(before,after,rtol=0,atol=1e-12)

    def test_all_models_share_exact_months(self):
        dates = self.f.groupby("model").month.apply(tuple)
        self.assertTrue(all(x == dates.iloc[0] for x in dates))
        self.assertEqual(len(dates.iloc[0]),18)

    def test_training_and_features_precede_target(self):
        for lag in [1,2]:
            f=forecast(self.p,self.a,availability_lag=lag)
            self.assertTrue((f.train_last_month <= f.latest_input_month).all())
            self.assertTrue((f.latest_input_month < f.month).all())
            self.assertTrue((f.train_n >= 10).all())

    def test_zero_forecast_has_no_direction_claim(self):
        m=summarize(self.f).set_index("model")
        self.assertTrue(pd.isna(m.loc["No change","direction_accuracy"]))
        self.assertEqual(m.loc["No change","direction_call_coverage"],0)

    def test_share_is_a_ratio_and_metrics_are_pp(self):
        np.testing.assert_allclose(self.p.nev_share,self.p.nev_retail_wan/self.p.retail_wan)
        g=self.f[self.f.model=="No change"]
        expected=self.p.set_index("month").nev_share.diff().loc[g.month].abs().mean()*100
        self.assertAlmostEqual(summarize(self.f).set_index("model").loc["No change","mae_pp"],expected)

    def test_input_target_month_change_does_not_change_its_prediction(self):
        month=pd.Timestamp("2025-08-01")
        p=self.p.copy();p.loc[p.month==month,"nev_share"] = .999
        changed=forecast(p,self.a)
        np.testing.assert_allclose(self.f.loc[self.f.month==month,"predicted_change_pp"],
                                   changed.loc[changed.month==month,"predicted_change_pp"])

    def test_tidy_model_and_manufacturer_keys(self):
        d=pd.read_csv(ROOT/"data/processed/model_sales_tidy.csv")
        self.assertFalse(d.duplicated(["brand","model","month"]).any())
        self.assertTrue(d.sales_units.isna().any())
        w=pd.read_csv(ROOT/"data/processed/manufacturer_wholesale_monthly.csv")
        self.assertFalse(w.duplicated(["manufacturer","month"]).any())
        self.assertEqual(w.month.nunique(),20)


if __name__ == "__main__":unittest.main()
