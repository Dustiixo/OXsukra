import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

import core
import imports


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.cx=core.db_open(Path(self.temp.name)/'test.db')
        imports.ensure_schema(self.cx)

    def tearDown(self):
        self.cx.close()
        self.temp.cleanup()

    def stage(self, text, profile='cash', account='ca_paypal', mapping=None):
        if mapping is None:
            mapping=imports.preview(text,profile)['mapping']
        return imports.stage(self.cx,dict(csv_text=text,filename='statement.csv',profile=profile,
                                          account=account,mapping=mapping))

    def records(self, account=None):
        q='SELECT * FROM import_records '+('WHERE account=? ' if account else '')+'ORDER BY id'
        return core.rows(self.cx,q,(account,) if account else ())

    def test_preview_and_automatic_header_mapping(self):
        text='Date,Transaction ID,Description,Net Amount,Currency,Status\n2026-11-07,TX1,Sale,"1,235.50",CAD,Completed\n'
        p=imports.preview(text,'cash')
        self.assertEqual(p['rows'],1)
        self.assertEqual(p['mapping']['amount'],'Net Amount')
        self.assertEqual(p['mapping']['reference'],'Transaction ID')
        out=self.stage(text)
        self.assertEqual(out['new_rows'],1)
        self.assertEqual(imports.report(self.cx)['batches'][0]['summary']['in_cents'],'1235.50')

    def test_cash_stage_does_not_change_balance_and_post_once(self):
        text='ID,Net,Status\nt1,100.00,Completed\nt2,-25.01,Completed\n'
        result=self.stage(text)
        self.assertEqual(result['new_rows'],2)
        self.assertEqual(core.balances(self.cx)['ca_paypal'],0)
        ids=[r['id'] for r in self.records()]
        imports.review(self.cx,ids[0],'cash_in')
        imports.review(self.cx,ids[1],'cash_out')
        self.assertEqual(core.balances(self.cx)['ca_paypal'],7499)
        with self.assertRaises(ValueError):imports.review(self.cx,ids[0],'cash_in')
        self.assertEqual(self.stage(text)['duplicate_rows'],2)
        self.assertEqual(core.balances(self.cx)['ca_paypal'],7499)

    def test_pending_and_reversed_cannot_be_posted(self):
        self.stage('ID,Net,Status\nt1,45,Pending\nt2,-20,Reversed\n')
        ids=[r['id'] for r in self.records()]
        for rid in ids:
            with self.assertRaises(ValueError):imports.review(self.cx,rid,'cash_in' if rid==ids[0] else 'cash_out')
        self.assertEqual(core.balances(self.cx)['ca_paypal'],0)

    def test_reference_match_does_not_double_post(self):
        core.add_event(self.cx,{'kind':'cash_in','target':'ca_paypal','amount':'80','reference':'statement-1'})
        self.stage('ID,Net,Status\nstatement-1,80,Completed\n')
        r=self.records()[0]
        res=imports.review(self.cx,r['id'],'match')
        self.assertEqual(res['state'],'matched')
        self.assertEqual(core.balances(self.cx)['ca_paypal'],8000)

    def test_currency_mismatch_rejected_and_other_rows_preserved(self):
        out=self.stage('ID,Net,Currency\na,20,NZD\nb,50,CAD\n')
        self.assertEqual((out['new_rows'],out['rejected_rows']),(1,1))
        self.assertEqual(len(imports.report(self.cx)['issues']),1)
        self.assertEqual(core.balances(self.cx)['ca_paypal'],0)

    def test_duplicate_id_different_cash_value_conflicts_not_overwritten(self):
        self.stage('ID,Net,Status\na,20,Completed\n')
        out=self.stage('ID,Net,Status\na,500,Completed\n')
        self.assertEqual(out['new_rows'],0)
        self.assertEqual(out['duplicate_rows'],1)
        self.assertIn('different values',imports.report(self.cx)['issues'][0]['message'])

    def test_bet_import_keeps_open_stake_then_later_settles(self):
        core.add_event(self.cx,{'kind':'cash_in','target':'ca_sports','amount':'100'})
        opened='Bet ID,Placed At,Stake,Payout,Status,Currency\nbet123,2026-11-07T10:00:00Z,20,,Open,CAD\n'
        settled='Bet ID,Placed At,Stake,Payout,Status,Currency\nbet123,2026-11-07T10:00:00Z,20,35,Settled,CAD\n'
        self.assertEqual(self.stage(opened,'bets','ca_sports')['new_rows'],1)
        self.assertEqual(core.balances(self.cx)['ca_sports'],10000)
        imports.review(self.cx,self.records()[0]['id'],'record_bet')
        self.assertEqual(core.balances(self.cx)['ca_sports'],8000)
        out=self.stage(settled,'bets','ca_sports')
        self.assertEqual(out['new_rows'],1)
        imports.review(self.cx,self.records()[1]['id'],'record_bet')
        self.assertEqual(core.balances(self.cx)['ca_sports'],11500)
        self.assertEqual(core.net_betting_profit(self.cx,'ca_sports'),1500)
        self.assertEqual(self.cx.execute('SELECT COUNT(*) FROM bets').fetchone()[0],1)
        self.assertEqual(self.stage(settled,'bets','ca_sports')['duplicate_rows'],1)

    def test_settled_wager_requires_payout_and_cannot_overdraw(self):
        out=self.stage('Bet ID,Stake,Status\nx1,12,Settled\n','bets','ca_sports')
        self.assertEqual(out['rejected_rows'],1)
        self.stage('Bet ID,Stake,Payout,Status\nx2,12,0,Lost\n','bets','ca_sports')
        with self.assertRaises(ValueError):imports.review(self.cx,self.records()[0]['id'],'record_bet')
        self.assertEqual(core.net_betting_profit(self.cx,'ca_sports'),0)

    def test_holdings_snapshot_is_not_buy_and_old_snapshots_rejected(self):
        text='As Of,Symbol,Asset Type,Quantity,Unit Price,Currency\n2026-11-07T20:10:00Z,SOL,crypto,2.5,100,USD\n'
        self.stage(text,'holdings','nz_crypto')
        self.assertEqual(core.balances(self.cx)['nz_crypto'],0)
        rid=self.records()[0]['id']
        imports.review(self.cx,rid,'update_holding')
        position=core.rows(self.cx,"SELECT * FROM positions WHERE account='nz_crypto'")[0]
        self.assertEqual(position['quantity'],'2.5')
        self.assertEqual(position['quote_currency'],'USD')
        self.assertEqual(position['source'],'statement_csv')
        self.assertEqual(core.balances(self.cx)['nz_crypto'],0)
        self.stage('As Of,Symbol,Quantity,Unit Price,Currency\n2026-11-05T20:00:00Z,SOL,3,90,USD\n', 'holdings','nz_crypto')
        with self.assertRaises(ValueError):imports.review(self.cx,self.records()[1]['id'],'update_holding')
        self.assertEqual(core.rows(self.cx,"SELECT quantity FROM positions WHERE symbol='SOL'")[0]['quantity'],'2.5')

    def test_ignored_row_can_be_restored(self):
        self.stage('ID,Net\nt1,10\n')
        rid=self.records()[0]['id']
        imports.review(self.cx,rid,'ignore')
        self.assertEqual(self.records()[0]['review_state'],'ignored')
        imports.review(self.cx,rid,'restore')
        self.assertEqual(self.records()[0]['review_state'],'staged')

    def test_invalid_csv_lengths_fields_and_money(self):
        for raw in ('A,A\n1,2\n', 'A,B\n1\n', 'A,B\n1,2,3\n', 'A,B\n"broken\n'):
            with self.assertRaises(ValueError):imports.preview(raw,'cash')
        bad=self.stage('ID,Net\na,"1,2"\n')
        self.assertEqual(bad['rejected_rows'],1)
        with self.assertRaises(ValueError):imports.preview('A,B\n'+'x,'+'y'*2_100_000,'cash')

    def test_no_external_id_preserves_repeated_legitimate_rows(self):
        text='Net,Status\n10,Completed\n10,Completed\n'
        first=self.stage(text)
        self.assertEqual(first['new_rows'],2)
        self.assertEqual(len(self.records()),2)
        again=self.stage(text)
        self.assertEqual(again['duplicate_rows'],2)
        self.assertEqual(len(self.records()),2)

    def test_holdings_valuation_separates_currency_and_snapshots(self):
        text='As Of,Symbol,Quantity,Unit Price,Currency\n2026-11-07T10:00:00Z,BTC,1,100000,NZD\n2026-11-07T11:00:00Z,BTC,2,110000,NZD\n2026-11-07T11:00:00Z,ETH,1,3000,USD\n'
        self.stage(text,'holdings','nz_crypto')
        summary=imports.report(self.cx)['batches'][0]['summary']
        self.assertEqual(summary['holding_symbols'],2)
        self.assertEqual(summary['holdings_by_currency'],{'NZD':'220000.00','USD':'3000.00'})
        self.assertEqual(core.balances(self.cx)['nz_crypto'],0)

    def test_duplicate_cash_id_does_not_change_five_way_pool(self):
        core.add_event(self.cx,{'kind':'cash_in','target':'ca_bank','amount':'150'})
        core.add_event(self.cx,{'kind':'transfer','source':'ca_bank','target':'ca_sports','amount':'100'})
        core.add_bet(self.cx,{'account':'ca_sports','category':'basketball','stake':'10'})
        core.settle_bet(self.cx,1,'20')
        core.set_play_rule(self.cx,{'account':'ca_sports','ceiling':'100'})
        before=core.sweep_candidate(self.cx,'ca_sports')
        self.stage('ID,Net,Status\nt1,900,Completed\n')
        self.assertEqual(core.sweep_candidate(self.cx,'ca_sports'),before)
        self.assertEqual(core.dashboard(self.cx)['pool']['proposed_max'],'0.00')


if __name__=='__main__':unittest.main()
