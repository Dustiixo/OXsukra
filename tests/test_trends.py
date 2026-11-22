import unittest
from watch_dashboard import render_trends


def snap(t, price, source='fixture', currency='CAD', name='Test'):
    return {'collected_at':t, 'observation':{'cards':[{'game':'MTG','name':name,'set_code':'abc','collector_number':'1','currency':currency,'source':source,'unit_price':price}]}}

class TrendTests(unittest.TestCase):
    def test_grouping_source_currency_and_gaps(self):
        data=[snap(1000,'1'),snap(1900,'2'),snap(5500,'3'),snap(6400,'4'),snap(6500,'8',source='other'),snap(6600,'9',currency='USD')]
        html=render_trends(data)
        self.assertIn('4 local observations; 1 gaps',html)
        self.assertEqual(html.count('<polyline'),2)
        self.assertNotIn('8 to 9',html)
    def test_escape_and_invalid_prices(self):
        data=[snap(1000,'NaN'),snap(1900,'1',name='<script>'),snap(2800,'2',name='<script>')]
        html=render_trends(data)
        self.assertIn('&lt;script&gt;',html)
        self.assertNotIn('<script>',html)
        self.assertEqual(html.count('<circle'),2)
    def test_empty_and_missing_identity(self):
        self.assertIn('No comparable history',render_trends([snap(1000,'1')]))
        self.assertIn('No comparable history',render_trends([snap(1000,'1',currency=''),snap(1900,'2',currency='')]))

if __name__=='__main__':unittest.main()
