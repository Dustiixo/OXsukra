import unittest
from watch_dashboard import render_trends, series_id


def snap(t, name, price):
    return {'collected_at':t,'observation':{'cards':[{'game':'MTG','name':name,'set_code':'abc','collector_number':'1','currency':'CAD','source':'fixture','unit_price':price}]}}

class StableSeriesTests(unittest.TestCase):
    def test_identity_survives_new_earlier_sorting_card(self):
        key=('MTG','B','abc','1','CAD','fixture')
        identity=series_id(key)
        initial=[snap(1000,'B','3'),snap(1900,'B','4')]
        later=[snap(1000,'A','1'),snap(1900,'A','2')]+initial
        self.assertEqual(render_trends(initial,identity).count('<polyline'),1)
        html=render_trends(later,identity)
        self.assertEqual(html.count('<polyline'),1)
        self.assertIn('B / abc',html)
        self.assertIn('value="'+identity+'" selected',html)
        self.assertIn('text-anchor="end"',html)
    def test_identity_includes_currency_and_source(self):
        a=('MTG','B','abc','1','CAD','fixture')
        self.assertNotEqual(series_id(a),series_id(a[:4]+('USD',)+a[5:]))
        self.assertNotEqual(series_id(a),series_id(a[:5]+('other',)))
