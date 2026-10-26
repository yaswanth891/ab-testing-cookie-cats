import unittest
import sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from analyze import validate,analyze,z_test

class TestAB(unittest.TestCase):
    def setUp(self):
        self.d=pd.DataFrame({'userid':range(1,9),'version':['gate_30']*4+['gate_40']*4,
                  'sum_gamerounds':[4,6,5,3,8,9,1,2],
                  'retention_1':[1,0,1,1,0,1,1,0],
                  'retention_7':[1,1,0,1,0,0,1,0]})
    def test_z_test_direction(self):
        x=z_test(50,100,30,100)
        self.assertAlmostEqual(x['difference_pp'],-20)
        self.assertLess(x['p_value'],.01)
        self.assertTrue(x['ci_low_pp']<x['difference_pp']<x['ci_high_pp'])
    def test_observed_rates(self):
        r=analyze(self.d)
        self.assertEqual(r['users'],8)
        self.assertAlmostEqual(r['day_7']['control_rate'],.75)
        self.assertAlmostEqual(r['day_7']['treatment_rate'],.25)
    def test_duplicate_user_rejected(self):
        x=self.d.copy();x.loc[1,'userid']=1
        with self.assertRaises(ValueError):validate(x)
    def test_invalid_flags_rejected(self):
        x=self.d.copy();x['retention_7']=x['retention_7'].astype(object);x.loc[1,'retention_7']='maybe'
        with self.assertRaises(ValueError):validate(x)
    def test_boolean_csv_strings(self):
        x=self.d.copy();x['retention_1']=x.retention_1.map({1:'True',0:'False'})
        self.assertEqual(validate(x).retention_1.sum(),5)

if __name__=='__main__':unittest.main()
