import sys
import unittest
import asyncio
import quamash
import time
import logging
from ucoinpy.documents.peer import BMAEndpoint as PyBMAEndpoint
from PyQt5.QtWidgets import QDialog, QDialogButtonBox
from PyQt5.QtCore import QLocale, Qt
from PyQt5.QtTest import QTest
from ucoinpy.api.bma import API
from cutecoin.tests.mocks.monkeypatch import pretender_reversed
from cutecoin.tests.mocks.bma import nice_blockchain
from cutecoin.core.registry.identities import IdentitiesRegistry
from cutecoin.gui.transfer import TransferMoneyDialog
from cutecoin.gui.password_asker import PasswordAskerDialog
from cutecoin.core.app import Application
from cutecoin.core import Account, Community, Wallet
from cutecoin.core.net import Network, Node
from ucoinpy.documents.peer import BMAEndpoint
from cutecoin.core.net.api.bma.access import BmaAccess
from cutecoin.tests import get_application
from ucoinpy.api import bma


class TestTransferDialog(unittest.TestCase):
    def setUp(self):
        self.qapplication = get_application()
        QLocale.setDefault(QLocale("en_GB"))
        self.lp = quamash.QEventLoop(self.qapplication)
        asyncio.set_event_loop(self.lp)
        self.identities_registry = IdentitiesRegistry({})

        self.application = Application(self.qapplication, self.lp, self.identities_registry)
        self.application.preferences['notifications'] = False

        self.endpoint = BMAEndpoint("", "127.0.0.1", "", 50000)
        self.node = Node("test_currency", [self.endpoint],
                         "", "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
                         None, Node.ONLINE,
                         time.time(), {}, "ucoin", "0.14.0", 0)
        self.network = Network.create(self.node)
        self.bma_access = BmaAccess.create(self.network)
        self.community = Community("test_currency", self.network, self.bma_access)

        self.wallet = Wallet(0, "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                             "Wallet 1", self.identities_registry)

        # Salt/password : "testcutecoin/testcutecoin"
        # Pubkey : 7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ
        self.account = Account("testcutecoin", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                               "john", [self.community], [self.wallet], [], self.identities_registry)

        self.password_asker = PasswordAskerDialog(self.account)
        self.password_asker.password = "testcutecoin"
        self.password_asker.remember = True

    def tearDown(self):
        try:
            self.lp.close()
        finally:
            asyncio.set_event_loop(None)

    def test_transfer_nice_community(self):
        mock = nice_blockchain.get_mock()
        time.sleep(2)
        logging.debug(mock.pretend_url)
        API.reverse_url = pretender_reversed(mock.pretend_url)
        transfer_dialog = TransferMoneyDialog(self.application,
                                                   self.account,
                                                   self.password_asker)

        @asyncio.coroutine
        def open_dialog(certification_dialog):
            result = yield from certification_dialog.async_exec()
            self.assertEqual(result, QDialog.Rejected)

        def close_dialog():
            if transfer_dialog.isVisible():
                transfer_dialog.close()

        @asyncio.coroutine
        def exec_test():
            yield from asyncio.sleep(1)
            QTest.mouseClick(transfer_dialog.radio_pubkey, Qt.LeftButton)
            QTest.keyClicks(transfer_dialog.edit_pubkey, "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn")
            QTest.mouseClick(transfer_dialog.button_box.button(QDialogButtonBox.Cancel), Qt.LeftButton)

        self.lp.call_later(15, close_dialog)
        asyncio.async(exec_test())
        self.lp.run_until_complete(open_dialog(transfer_dialog))
        mock.delete_mock()


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()
