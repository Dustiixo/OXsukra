import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cx = core.db_open(Path(self.temp.name)/'treasury.db')

    def tearDown(self):
        self.cx.close()
        self.temp.cleanup()

    def test_seed_accounts_are_empty_and_unverified(self):
        dashboard=core.dashboard(self.cx)
        self.assertEqual(len(dashboard['accounts']),7)
        self.assertTrue(all(a['verified']=='unverified' for a in dashboard['accounts']))
        self.assertTrue(all(a['balance']=='0.00' for a in dashboard['accounts']))

    def test_transfer_and_settlement_profit_invariant(self):
        core.add_event(self.cx,dict(kind='cash_in',target='ca_bank',amount='100'))
        core.add_event(self.cx,dict(kind='transfer',source='ca_bank',target='ca_sports',amount='30'))
        bet=core.add_bet(self.cx,dict(account='ca_sports',stake='10',category='Horse racing'))
        self.assertEqual(core.dashboard(self.cx)['open_risk']['CAD'],'10.00')
        core.settle_bet(self.cx,bet,'17.50')
        core.add_event(self.cx,dict(kind='transfer',source='ca_sports',target='ca_paypal',amount='7.50'))
        d=core.dashboard(self.cx)
        self.assertEqual(d['pnl']['CAD'],'7.50')
        self.assertEqual(d['open_risk']['CAD'],'0.00')
        self.assertEqual(d['pool']['proposed_max'],'0.00')  # Ordinary transfers are not confirmed sweeps
        self.assertEqual(sum(core.cents(a['balance']) for a in d['accounts'] if a['currency']=='CAD'),10750)

    def test_loss_does_not_create_pool(self):
        core.add_event(self.cx,dict(kind='cash_in',target='ca_sports',amount='30'))
        core.add_event(self.cx,dict(kind='cash_in',target='ca_paypal',amount='100'))
        bet=core.add_bet(self.cx,dict(account='ca_sports',stake='10',category='Basketball'))
        core.settle_bet(self.cx,bet,'0')
        self.assertEqual(core.dashboard(self.cx)['pool']['proposed_max'],'0.00')
        self.assertEqual(core.dashboard(self.cx)['pnl']['CAD'],'-10.00')

    def test_fx_does_not_create_gambling_profit(self):
        core.add_event(self.cx,dict(kind='cash_in',target='ca_bank',amount='100'))
        core.add_event(self.cx,dict(kind='fx_transfer',source='ca_bank',target='au_bank',amount='30',target_amount='31.20'))
        d=core.dashboard(self.cx)
        self.assertEqual(next(a['balance'] for a in d['accounts'] if a['id']=='au_bank'),'31.20')
        self.assertEqual(d['pnl']['CAD'],'0.00')
        self.assertEqual(d['pool']['proposed_max'],'0.00')

    def test_no_cross_currency_plain_transfer(self):
        core.add_event(self.cx,dict(kind='cash_in',target='ca_bank',amount='100'))
        with self.assertRaisesRegex(ValueError,'Same-currency'):
            core.add_event(self.cx,dict(kind='transfer',source='ca_bank',target='au_bank',amount='10'))
        with self.assertRaisesRegex(ValueError,'Explicit received'):
            core.add_event(self.cx,dict(kind='fx_transfer',source='ca_bank',target='au_bank',amount='10'))

    def test_cannot_spend_untracked_cash(self):
        with self.assertRaisesRegex(ValueError,'Insufficient'):
            core.add_bet(self.cx,dict(account='ca_sports',stake='5',category='Greyhound'))
        with self.assertRaisesRegex(ValueError,'Insufficient'):
            core.add_event(self.cx,dict(kind='cash_out',source='ca_paypal',amount='10'))

    def test_stake_can_only_be_settled_once(self):
        core.add_event(self.cx,dict(kind='cash_in',target='ca_sports',amount='20'))
        bet=core.add_bet(self.cx,dict(account='ca_sports',stake='5',category='Other'))
        core.settle_bet(self.cx,bet,'0')
        with self.assertRaisesRegex(ValueError,'already settled'):
            core.settle_bet(self.cx,bet,'10')

    def test_reference_is_unique(self):
        row=dict(kind='cash_in',target='ca_paypal',amount='10',reference='tx-123')
        core.add_event(self.cx,row)
        with self.assertRaises(Exception):
            core.add_event(self.cx,row)
        self.assertEqual(next(a['balance'] for a in core.dashboard(self.cx)['accounts'] if a['id']=='ca_paypal'),'10.00')

    def test_manual_position_and_non_cash_valuation(self):
        core.add_position(self.cx,dict(account='nz_crypto',symbol='BTC',asset_type='crypto',quantity='0.5',unit_price='100000',quote_currency='NZD'))
        d=core.dashboard(self.cx)
        self.assertEqual(d['positions'][0]['market_value'],'50000.00')
        self.assertEqual(d['pool']['proposed_max'],'0.00')

    def test_buffer_hold_release_does_not_change_cash_or_profit(self):
        core.add_event(self.cx,dict(kind='cash_in',target='ca_bank',amount='100'))
        core.buffer_action(self.cx,dict(account='ca_bank',purpose='betting',action='hold',amount='25'))
        d=core.dashboard(self.cx)
        bank=next(a for a in d['accounts'] if a['id']=='ca_bank')
        self.assertEqual((bank['balance'], bank['held'], bank['available']),('100.00','25.00','75.00'))
        self.assertEqual(d['pnl']['CAD'],'0.00')
        with self.assertRaisesRegex(ValueError,'Insufficient unheld'):
            core.add_event(self.cx,dict(kind='transfer',source='ca_bank',target='ca_sports',amount='80'))
        core.buffer_action(self.cx,dict(account='ca_bank',purpose='betting',action='release',amount='10'))
        core.add_event(self.cx,dict(kind='transfer',source='ca_bank',target='ca_sports',amount='80'))
        d=core.dashboard(self.cx)
        bank=next(a for a in d['accounts'] if a['id']=='ca_bank')
        self.assertEqual((bank['balance'],bank['held'],bank['available']),('20.00','15.00','5.00'))
        self.assertEqual(d['pnl']['CAD'],'0.00')

    def test_buffers_cannot_overdraw_or_overrelease(self):
        core.add_event(self.cx,dict(kind='cash_in',target='ca_paypal',amount='25'))
        core.buffer_action(self.cx,dict(account='ca_paypal',purpose='investing',action='hold',amount='20'))
        with self.assertRaisesRegex(ValueError,'Insufficient unheld'):
            core.buffer_action(self.cx,dict(account='ca_paypal',purpose='betting',action='hold',amount='10'))
        with self.assertRaisesRegex(ValueError,'Cannot release'):
            core.buffer_action(self.cx,dict(account='ca_paypal',purpose='betting',action='release',amount='10'))
        with self.assertRaisesRegex(ValueError,'Cannot release'):
            core.buffer_action(self.cx,dict(account='ca_paypal',purpose='investing',action='release',amount='21'))
        self.assertEqual(core.dashboard(self.cx)['pool']['buffer_held'],'20.00')

    def test_buffer_reduces_pool_but_never_creates_profit(self):
        core.add_event(self.cx,dict(kind='cash_in',target='ca_paypal',amount='100'))
        core.add_event(self.cx,dict(kind='cash_in',target='ca_sports',amount='20'))
        bet=core.add_bet(self.cx,dict(account='ca_sports',stake='10',category='Other'))
        core.settle_bet(self.cx,bet,'15')
        # Only a verified user-recorded profit sweep enters the proposed pool.
        self.assertEqual(core.dashboard(self.cx)['pool']['proposed_max'],'0.00')
        core.update_settings(self.cx,dict(pool_source='ca_paypal',cash_floor='0',
            weight_stocks='50',weight_crypto='15',weight_reserve='20',weight_fun='10',weight_wager='5',auto_earmark='0'))
        core.set_play_rule(self.cx,dict(account='ca_sports',ceiling='20'))
        core.add_event(self.cx,dict(kind='profit_sweep',source='ca_sports',target='ca_paypal',amount='5'))
        self.assertEqual(core.dashboard(self.cx)['pool']['proposed_max'],'5.00')
        core.buffer_action(self.cx,dict(account='ca_paypal',purpose='reserve',action='hold',amount='103'))
        self.assertEqual(core.dashboard(self.cx)['pool']['proposed_max'],'2.00')
        core.buffer_action(self.cx,dict(account='ca_paypal',purpose='reserve',action='release',amount='3'))
        self.assertEqual(core.dashboard(self.cx)['pool']['proposed_max'],'5.00')

    def test_five_way_sweep_commits_once_and_buffers_each_bucket(self):
        core.add_event(self.cx,dict(kind='cash_in',target='ca_sports',amount='100'))
        core.set_play_rule(self.cx,dict(account='ca_sports',ceiling='100'))
        bet=core.add_bet(self.cx,dict(account='ca_sports',stake='10',category='Basketball'))
        core.settle_bet(self.cx,bet,'80')  # Net $70
        self.assertEqual(core.sweep_candidate(self.cx,'ca_sports'),7000)
        core.add_event(self.cx,dict(kind='profit_sweep',source='ca_sports',target='ca_paypal',amount='70'))
        d=core.dashboard(self.cx)
        self.assertEqual(d['pool']['proposed_max'],'0.00')
        self.assertEqual(d['pool']['already_earmarked'],'70.00')
        self.assertEqual(d['pool']['buffer_held'],'70.00')
        self.assertEqual(core.sweep_candidate(self.cx,'ca_sports'),0)
        self.assertEqual(len(d['allocation_commits']),1)
        alloc=d['allocation_commits'][0]
        self.assertEqual({key:alloc[key] for key in ('stocks','crypto','reserve','fun','wager')},
                         {'stocks':'35.00','crypto':'10.50','reserve':'14.00','fun':'7.00','wager':'3.50'})
        self.assertEqual({x['purpose']:x['held'] for x in d['buffers']},
                         {'shares':'35.00','crypto':'10.50','reserve':'14.00','fun':'7.00','betting':'3.50'})
        with self.assertRaisesRegex(ValueError,'exceeds'):
            core.add_event(self.cx,dict(kind='profit_sweep',source='ca_sports',target='ca_paypal',amount='1'))
        with self.assertRaisesRegex(ValueError,'Insufficient unheld'):
            core.add_event(self.cx,dict(kind='transfer',source='ca_paypal',target='ca_sports',amount='1'))

    def test_share_focus_and_rounding_preserve_each_cent(self):
        settings=core.dashboard(self.cx)['settings']
        self.assertEqual([int(settings['weight_'+k]) for k in ('stocks','crypto','reserve','fun','wager')],[50,15,20,10,5])
        for amount in (1,2,13,101,100001):
            split=core._split_allocations(amount,settings)
            self.assertEqual(sum(split.values()),amount)
            self.assertTrue(all(v>=0 for v in split.values()))
        with self.assertRaisesRegex(ValueError,'total 100'):
            core.update_settings(self.cx,dict(pool_source='ca_paypal',cash_floor='0',
                weight_stocks='50',weight_crypto='15',weight_reserve='20',weight_fun='10',weight_wager='6'))
        no_stocks={**settings,'weight_stocks':'0','weight_crypto':'75',
                   'weight_reserve':'20','weight_fun':'5','weight_wager':'0'}
        for amount in (1,3,97):
            alloc=core._split_allocations(amount,no_stocks)
            self.assertEqual(alloc['stocks'],0)
            self.assertEqual(alloc['wager'],0)
            self.assertEqual(sum(alloc.values()),amount)

    def test_upgrade_old_schema_keeps_existing_three_bucket_commits(self):
        import sqlite3
        oldpath=Path(self.temp.name)/'legacy.db'
        legacy=core.db_open(oldpath)
        core.add_event(legacy,dict(kind='cash_in',target='ca_paypal',amount='20'))
        legacy.executescript("""
        DROP TABLE allocation_commits;
        CREATE TABLE allocation_commits (
            id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL,
            account TEXT NOT NULL REFERENCES accounts(id),
            amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
            reserve_cents INTEGER NOT NULL CHECK(reserve_cents >= 0),
            stocks_cents INTEGER NOT NULL CHECK(stocks_cents >= 0),
            crypto_cents INTEGER NOT NULL CHECK(crypto_cents >= 0),
            source_event INTEGER NOT NULL UNIQUE REFERENCES events(id),
            CHECK(amount_cents = reserve_cents + stocks_cents + crypto_cents)
        );
        INSERT INTO allocation_commits
           (at,account,amount_cents,reserve_cents,stocks_cents,crypto_cents,source_event)
        VALUES('2026-01-01','ca_paypal',2000,1000,600,400,1);
        DROP TABLE buffer_actions;
        CREATE TABLE buffer_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            at TEXT NOT NULL, account TEXT NOT NULL REFERENCES accounts(id),
            purpose TEXT NOT NULL CHECK(purpose IN ('betting','investing','reserve')),
            action TEXT NOT NULL CHECK(action IN ('hold','release')),
            amount_cents INTEGER NOT NULL CHECK(amount_cents > 0), memo TEXT NOT NULL DEFAULT ''
        );
        INSERT INTO buffer_actions(at,account,purpose,action,amount_cents)
        VALUES('2026-01-01','ca_paypal','investing','hold',1000);
        DELETE FROM settings WHERE key IN ('weight_fun','weight_wager');
        UPDATE settings SET value='50' WHERE key='weight_reserve';
        UPDATE settings SET value='30' WHERE key='weight_stocks';
        UPDATE settings SET value='20' WHERE key='weight_crypto';
        """)
        legacy.close()
        migrated=core.db_open(oldpath)
        try:
            d=core.dashboard(migrated)
            self.assertEqual(d['allocation_commits'][0]['amount'],'20.00')
            self.assertEqual(d['allocation_commits'][0]['fun'],'0.00')
            self.assertEqual(d['allocation_commits'][0]['wager'],'0.00')
            self.assertEqual(d['settings']['weight_stocks'],'50')
            self.assertEqual(d['settings']['weight_fun'],'10')
            core.buffer_action(migrated,dict(account='ca_paypal',purpose='fun',action='hold',amount='2'))
        finally:
            migrated.close()

    def test_weights_require_exact_total(self):
        with self.assertRaisesRegex(ValueError,'total 100'):
            core.update_settings(self.cx,dict(pool_source='ca_paypal',cash_floor='0',weight_reserve='60',weight_stocks='30',weight_crypto='20'))


if __name__=='__main__': unittest.main()
