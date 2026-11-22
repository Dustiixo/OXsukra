import tempfile
from pathlib import Path
import unittest
from sold_research import import_csv, read_sales
from sale_review import annotate

class SaleReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.db=Path(self.temp.name)/'tracker.db'
        self.csv=Path(__file__).resolve().parents[1]/'samples'/'claimed_sales_fictional.csv'
        import_csv(self.db,self.csv)
        self.first=read_sales(self.db)[0]

    def review(self, decision='needs_review', note='Source document requires checking'):
        return annotate(self.db,self.first['marketplace'],self.first['sale_id'],decision,note)

    def test_review_is_annotation_not_verification(self):
        self.review('document_seen','Local screenshot inspected, no independent verification')
        record=read_sales(self.db)[0]
        self.assertEqual(record['review']['decision'],'document_seen')
        self.assertEqual(record['verification_status'],'unverified')
        self.assertEqual(record['review']['note'],'Local screenshot inspected, no independent verification')

    def test_review_latest_wins_without_rewriting_history(self):
        self.review();self.review('excluded','Listing is not a completed transaction')
        self.assertEqual(read_sales(self.db)[0]['review']['decision'],'excluded')
        from sold_research import connect
        with connect(self.db) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM sale_review').fetchone()[0],2)

    def test_invalid_and_unknown_do_not_create_reviews(self):
        with self.assertRaises(ValueError): self.review('verified','No')
        with self.assertRaises(ValueError): self.review(note='bad\nline')
        with self.assertRaises(ValueError): annotate(self.db,'Unknown','not-a-sale','excluded','No match')
        self.assertIsNone(read_sales(self.db)[0]['review'])

    def test_reimport_preserves_review_and_duplicate_behavior(self):
        self.review('disputed','Evidence conflicts with sale date')
        self.assertEqual(import_csv(self.db,self.csv)['imported'],0)
        self.assertEqual(read_sales(self.db)[0]['review']['decision'],'disputed')

    def test_missing_db_not_created(self):
        path=Path(self.temp.name)/'missing.db'
        with self.assertRaises(ValueError):annotate(path,'x','y','excluded','Not present')
        self.assertFalse(path.exists())
