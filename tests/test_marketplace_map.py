"""Fictional eBay own-orders fixture: no external requests, accounts or private data."""
import csv
from pathlib import Path
import tempfile
import unittest

from marketplace_map import (REQUIRED_EXPORT, ANNOTATION_FIELDS, inspect_export,
                             convert, export_normalized)
from sold_research import import_csv, read_sales


def make_csv(path, fields, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader();w.writerows(rows)


class MarketplaceMapTests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup)
        self.root=Path(d.name)
        self.source=self.root/'source.csv'
        self.notes=self.root/'notes.csv'
        self.output=self.root/'normalized.csv'
        self.db=self.root/'tracked.db'
        self.source_rows=[dict(zip(REQUIRED_EXPORT, ('ORDER-1','123456789012','TXN-A','Fictional Foil', '$22.50','1','Nov 20, 2026'))),
                          dict(zip(REQUIRED_EXPORT, ('ORDER-2','123456789013','TXN-B','Fictional Non-card','$7.00','1','2026-11-20')))]
        for r in self.source_rows:
            r['Buyer Email']='private@example.invalid';r['Ship To Address 1']='PRIVATE STREET';r['Buyer Name']='PRIVATE NAME'
        self.note_rows=[dict(zip(ANNOTATION_FIELDS, ('ORDER-1','123456789012','TXN-A','MTG','Demo Card','DMO','001','Near Mint','https://example.com/fictional-reference')))]
        self.write()
    def write(self):
        make_csv(self.source,[*REQUIRED_EXPORT,'Buyer Email','Ship To Address 1','Buyer Name'],self.source_rows)
        make_csv(self.notes,ANNOTATION_FIELDS,self.note_rows)

    def test_inspect_only_does_not_create_output_or_database(self):
        info=inspect_export(self.source)
        self.assertEqual(info['row_count'],2)
        self.assertTrue(info['has_sensitive_columns'])
        self.assertFalse(self.output.exists())
        self.assertFalse(self.db.exists())
        self.assertNotIn('private@example',str(info))

    def test_private_fields_removed_and_actual_money_not_mutated(self):
        info=export_normalized(self.source,self.notes,'CAD',self.output)
        raw=self.output.read_text()
        for private in ('PRIVATE NAME','PRIVATE STREET','private@example.invalid','ORDER-1','TXN-A'):
            self.assertNotIn(private,raw)
        self.assertEqual(info['normalized_claims'],1)
        self.assertEqual(info['skipped_unannotated'],1)
        self.assertEqual(info['verification_status'],'unverified')
        self.assertFalse(self.db.exists())
        with self.output.open() as f:
            row=list(csv.DictReader(f))[0]
        self.assertEqual(row['currency'],'CAD')
        self.assertEqual(row['price'],'22.50')
        self.assertTrue(row['sale_id'].startswith('ebay-own-'))
        # Only an explicit import to the separate tracker database can create a claim.
        imported=import_csv(self.db,self.output)
        self.assertEqual(imported['imported'],1)
        self.assertEqual(read_sales(self.db)[0]['verification_status'],'unverified')

    def test_duplicate_run_preserves_previous_output(self):
        export_normalized(self.source,self.notes,'NZD',self.output)
        before=self.output.read_bytes()
        with self.assertRaises(FileExistsError):
            export_normalized(self.source,self.notes,'CAD',self.output)
        self.assertEqual(self.output.read_bytes(),before)

    def test_rejects_unreliable_quantity_and_date_without_output(self):
        self.source_rows[0]['Quantity']='2';self.write()
        with self.assertRaisesRegex(ValueError,'multi-quantity'):
            export_normalized(self.source,self.notes,'CAD',self.output)
        self.source_rows[0]['Quantity']='1';self.source_rows[0]['Sale Date']='bad date';self.write()
        with self.assertRaisesRegex(ValueError,'Sale Date'):
            export_normalized(self.source,self.notes,'CAD',self.output)
        self.assertFalse(self.output.exists())

    def test_unknown_annotations_and_duplicates_rejected(self):
        self.note_rows[0]['order_number']='NOT PRESENT';self.write()
        with self.assertRaisesRegex(ValueError,'absent'):
            convert(self.source,self.notes,'CAD')
        self.note_rows[0]['order_number']='ORDER-1';self.note_rows.append(self.note_rows[0].copy());self.write()
        with self.assertRaisesRegex(ValueError,'duplicated annotation'):
            convert(self.source,self.notes,'CAD')

    def test_formula_and_invalid_currency_rejected(self):
        self.note_rows[0]['name']='=HYPERLINK("https://bad.example")';self.write()
        with self.assertRaisesRegex(ValueError,'formula'):
            convert(self.source,self.notes,'CAD')
        self.note_rows[0]['name']='Demo Card';self.write()
        with self.assertRaisesRegex(ValueError,'currency'):
            convert(self.source,self.notes,'XYZ')

    def test_rejects_private_link_query_tokens(self):
        self.note_rows[0]['source_url']='https://example.com/private/receipt?token=redacted'
        self.write()
        with self.assertRaisesRegex(ValueError,'public link'):
            convert(self.source,self.notes,'CAD')
        self.assertFalse(self.output.exists())

    def test_refuses_missing_identifiers_or_conflicting_export(self):
        self.source_rows[0]['Transaction ID']='';self.write()
        with self.assertRaisesRegex(ValueError,'identity'):
            convert(self.source,self.notes,'CAD')
        self.source_rows[0]['Transaction ID']='TXN-A'
        self.source_rows.append(self.source_rows[0].copy());self.write()
        with self.assertRaisesRegex(ValueError,'repeated'):
            convert(self.source,self.notes,'CAD')

    def test_normalization_stable_under_extra_private_fields(self):
        records,report=convert(self.source,self.notes,'CAD')
        self.source_rows[0]['Buyer Email']='some-other-private@example.invalid';self.write()
        records2,report2=convert(self.source,self.notes,'CAD')
        self.assertEqual(records,records2)
        self.assertNotEqual(report['source_export_sha256'],report2['source_export_sha256'])


if __name__=='__main__':unittest.main()
