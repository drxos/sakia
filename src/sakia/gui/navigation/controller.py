from .model import NavigationModel
from .view import NavigationView
from sakia.models.generic_tree import GenericTreeModel
from .txhistory.controller import TxHistoryController
from .homescreen.controller import HomeScreenController
from .network.controller import NetworkController
from .identities.controller import IdentitiesController
from .informations.controller import InformationsController
from .graphs.wot.controller import WotController
from sakia.data.entities import Connection
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtWidgets import QMenu, QAction, QMessageBox, QDialog, QFileDialog
from PyQt5.QtGui import QCursor
from sakia.decorators import asyncify
from sakia.gui.password_asker import PasswordAskerDialog
from sakia.gui.widgets.dialogs import QAsyncMessageBox
from sakia.gui.widgets import toast


class NavigationController(QObject):
    """
    The navigation panel
    """
    currency_changed = pyqtSignal(str)
    connection_changed = pyqtSignal(Connection)

    def __init__(self, parent, view, model):
        """
        Constructor of the navigation component

        :param sakia.gui.navigation.view.NavigationView view: the view
        :param sakia.gui.navigation.model.NavigationModel model: the model
        """
        super().__init__(parent)
        self.view = view
        self.model = model
        self.components = {
            'TxHistory': TxHistoryController,
            'HomeScreen': HomeScreenController,
            'Network': NetworkController,
            'Identities': IdentitiesController,
            'Informations': InformationsController,
            'Wot': WotController
        }
        self.view.current_view_changed.connect(self.handle_view_change)
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.tree_context_menu)
        self._components_controllers = []

    @classmethod
    def create(cls, parent, app):
        """
        Instanciate a navigation component
        :param sakia.app.Application app: the application
        :return: a new Navigation controller
        :rtype: NavigationController
        """
        view = NavigationView(None)
        model = NavigationModel(None, app)
        navigation = cls(parent, view, model)
        model.setParent(navigation)
        navigation.init_navigation()
        app.new_connection.connect(navigation.add_connection)
        return navigation

    def parse_node(self, node_data):
        if 'component' in node_data:
            component_class = self.components[node_data['component']]
            component = component_class.create(self, self.model.app, **node_data['dependencies'])
            self._components_controllers.append(component)
            widget = self.view.add_widget(component.view)
            node_data['widget'] = widget
        if 'children' in node_data:
            for child in node_data['children']:
                self.parse_node(child)

    def init_navigation(self):
        self.model.init_navigation_data()

        for node in self.model.navigation:
            self.parse_node(node)

        self.view.set_model(self.model)

    def handle_view_change(self, raw_data):
        """
        Handle view change
        :param dict raw_data:
        :return:
        """
        user_identity = raw_data.get('user_identity', None)
        currency = raw_data.get('currency', None)
        if user_identity != self.model.current_data('user_identity'):
            self.account_changed.emit(user_identity)
        if currency != self.model.current_data('currency'):
            self.currency_changed.emit(currency)
        self.model.set_current_data(raw_data)

    def add_connection(self, connection):
        raw_node = self.model.add_connection(connection)
        self.view.add_connection(raw_node)
        self.parse_node(raw_node)

    def tree_context_menu(self, point):
        mapped = self.view.tree_view.mapFromParent(point)
        index = self.view.tree_view.indexAt(mapped)
        raw_data = self.view.tree_view.model().data(index, GenericTreeModel.ROLE_RAW_DATA)
        if raw_data and raw_data["component"] == "Informations":
            menu = QMenu(self.view)
            action_gen_revokation = QAction(self.tr("Save revokation document"), menu)
            menu.addAction(action_gen_revokation)
            action_gen_revokation.triggered.connect(lambda c:
                                                    self.action_save_revokation(raw_data['misc']['connection']))

            action_publish_uid = QAction(self.tr("Publish UID"), menu)
            menu.addAction(action_publish_uid)
            action_publish_uid.triggered.connect(lambda c:
                                                    self.publish_uid(raw_data['misc']['connection']))
            action_publish_uid.setEnabled(self.model.identity_published(raw_data['misc']['connection']))

            action_leave = QAction(self.tr("Leave the currency"), menu)
            menu.addAction(action_leave)
            action_leave.triggered.connect(lambda c: self.send_leave(raw_data['misc']['connection']))
            action_leave.setEnabled(self.model.identity_is_member(raw_data['misc']['connection']))

            action_remove = QAction(self.tr("Remove the connection"), menu)
            menu.addAction(action_remove)
            action_remove.triggered.connect(lambda c: self.remove_connection(raw_data['misc']['connection']))
            # Show the context menu.

            menu.popup(QCursor.pos())

    @asyncify
    async def publish_uid(self, connection):
        password = await self.password_asker.async_exec()
        if self.password_asker.result() == QDialog.Rejected:
            return
        result = await self.account.send_selfcert(password, self.community)
        if result[0]:
            if self.app.preferences['notifications']:
                toast.display(self.tr("UID"), self.tr("Success publishing your UID"))
            else:
                await QAsyncMessageBox.information(self, self.tr("Membership"),
                                                        self.tr("Success publishing your UID"))
        else:
            if self.app.preferences['notifications']:
                toast.display(self.tr("UID"), result[1])
            else:
                await QAsyncMessageBox.critical(self, self.tr("UID"),
                                                        result[1])

    @asyncify
    async def send_leave(self):
        reply = await QAsyncMessageBox.warning(self, self.tr("Warning"),
                                               self.tr("""Are you sure ?
Sending a leaving demand  cannot be canceled.
The process to join back the community later will have to be done again.""")
                                               .format(self.account.pubkey), QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            password = PasswordAskerDialog(self.model.navigation_model.navigation.current_connection()).async_exec()
            if not password:
                return
            result = await self.model.send_leave(password)
            if result[0]:
                if self.app.preferences['notifications']:
                    toast.display(self.tr("Revoke"), self.tr("Success sending Revoke demand"))
                else:
                    await QAsyncMessageBox.information(self, self.tr("Revoke"),
                                                       self.tr("Success sending Revoke demand"))
            else:
                if self.app.preferences['notifications']:
                    toast.display(self.tr("Revoke"), result[1])
                else:
                    await QAsyncMessageBox.critical(self, self.tr("Revoke"),
                                                    result[1])

    @asyncify
    async def remove_connection(self, connection):
        reply = await QAsyncMessageBox.question(self.view, self.tr("Removing the connection"),
                                                self.tr("""Are you sure ? This won't remove your money"
neither your identity from the network."""), QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            await self.model.remove_connection(connection)
            self.init_navigation()

    def action_save_revokation(self, connection):
        password = PasswordAskerDialog(connection).exec()
        if not password:
            return

        raw_document = self.model.generate_revokation(connection, password)
        # Testable way of using a QFileDialog
        selected_files = QFileDialog.getSaveFileName(self.view, self.tr("Save a revokation document"),
                                                       "", self.tr("All text files (*.txt)"))
        if selected_files:
            path = selected_files[0]
            if not path.endswith('.txt'):
                path = "{0}.txt".format(path)
            with open(path, 'w') as save_file:
                save_file.write(raw_document)

        dialog = QMessageBox(QMessageBox.Information, self.tr("Revokation file"),
                             self.tr("""<div>Your revokation document has been saved.</div>
<div><b>Please keep it in a safe place.</b></div>
The publication of this document will remove your identity from the network.</p>"""), QMessageBox.Ok)
        dialog.setTextFormat(Qt.RichText)
        dialog.exec()
