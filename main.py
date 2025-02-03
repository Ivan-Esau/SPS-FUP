#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logikgatter Simulator – FUP Lernapplikation im TIA-Portal-Stil (Dark Mode)
===========================================================================
Dieses Programm simuliert die Grundlagen der FUP-Programmierung (wie im Siemens TIA Portal)
und bietet:
  • Eine moderne, intuitive Oberfläche im Dark Mode mit einer Zeichenfläche (Canvas) in mehreren Netzwerken,
    die untereinander in einer ScrollArea angezeigt werden.
  • Logikbausteine: AND, OR, XOR, SR, =, TON, TOF, FP, FN – per Drag & Drop aus einer Palette.
  • Ein Variablenpanel mit vordefinierten Variablen (Eingänge, Ausgänge, Merker); Variablen werden nicht automatisch an Ports zugewiesen.
      Über das Kontextmenü können Variablen gelöscht oder bearbeitet werden.
  • Verbindungen zwischen Elementen:
      – Ein Klick an einem Port startet den Verbindungsmodus (temporäre, gelb gestrichelte Linie).
      – Ein weiterer Klick an einem kompatiblen Zielport verbindet die Elemente.
      – Doppelklick an einem Port öffnet den Zuordnungsdialog.
      – Rechtsklick an einem Port öffnet ein Kontextmenü zum Umschalten der Negation (Anzeige eines großen ¬ in Orange).
      – Rechtsklick an einer Verbindung löscht diese.
  • Netzwerke werden vertikal in einer ScrollArea angezeigt, jedes mit Header (Name und Lösch-Button).
      Neue Gate‑Elemente werden automatisch so positioniert, dass sie nicht zu nahe an anderen liegen.
  • Mit der Entf-Taste lassen sich ausgewählte Elemente löschen.
  • Die Simulation läuft live (über einen Timer, der alle 200 ms die Logik neu auswertet).
  • Der "Simulieren"-Button öffnet ein Fenster zur Steuerung der Eingänge – dieses erscheint in der unteren linken Ecke.

Instruktionen (Statusleiste):
  • Variablen erstellen: Klicke im Variablenpanel auf "+"
  • Variable zuweisen: Doppelklick an einem Port öffnet den Zuordnungsdialog.
  • Verbindung: Ein Klick startet den Verbindungsmodus, ein weiterer klick verbindet.
  • Rechtsklick an einem Port: Umschalten der Negation (zeigt ¬ an, Label in Orange).
  • Rechtsklick an einer Verbindung: Löscht diese.
  • Mit "Entf" werden ausgewählte Komponenten gelöscht.
  • Neues Netzwerk hinzufügen: Klicke auf "Neues Netzwerk" in der Toolbar.
  • Netzwerk löschen: Über den Lösch-Button im Header.
  • Simulation: Das Fenster "Eingänge steuern" ermöglicht das Live-Umschalten der Eingangswerte.
"""

import sys, time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsTextItem,
    QVBoxLayout, QWidget, QListWidget, QListWidgetItem, QDockWidget, QDialog,
    QLineEdit, QFormLayout, QPushButton, QLabel, QComboBox, QScrollArea,
    QHBoxLayout, QMenu, QToolBar
)
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QDrag, QPalette, QKeySequence
from PyQt5.QtCore import Qt, QPointF, QMimeData, QTimer

# Globales Dictionary für Variablen
VARIABLES = {}


# -----------------------------------------------------------------------------
# Datenstruktur: Variable
# -----------------------------------------------------------------------------

class Variable:
    """Repräsentiert eine Variable (Eingang, Ausgang, Merker) mit einem binären Wert."""

    def __init__(self, name, var_type, value=False):
        self.name = name
        self.var_type = var_type.lower()
        self.value = value


# -----------------------------------------------------------------------------
# Dialoge
# -----------------------------------------------------------------------------

class NewVariableDialog(QDialog):
    """Dialog zur Erstellung einer neuen Variable."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neue Variable erstellen")
        self.setStyleSheet("""
            QLabel { color: white; }
            QLineEdit, QComboBox, QPushButton { background-color: #555555; color: white; }
        """)
        layout = QFormLayout(self)
        self.name_edit = QLineEdit(self)
        layout.addRow("Name:", self.name_edit)
        self.type_combo = QComboBox(self)
        self.type_combo.addItems(["Eingang", "Ausgang", "Merker"])
        layout.addRow("Typ:", self.type_combo)
        self.value_combo = QComboBox(self)
        self.value_combo.addItems(["0", "1"])
        layout.addRow("Wert:", self.value_combo)
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

    def get_values(self):
        name = self.name_edit.text().strip()
        var_type = self.type_combo.currentText()
        value = True if self.value_combo.currentText() == "1" else False
        return name, var_type, value


class EditVariableDialog(QDialog):
    """Dialog zur Bearbeitung einer Variable."""

    def __init__(self, var, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Variable bearbeiten")
        self.setStyleSheet("""
            QLabel { color: white; }
            QLineEdit, QComboBox, QPushButton { background-color: #555555; color: white; }
        """)
        layout = QFormLayout(self)
        self.name_edit = QLineEdit(self)
        self.name_edit.setText(var.name)
        layout.addRow("Name:", self.name_edit)
        self.type_combo = QComboBox(self)
        self.type_combo.addItems(["Eingang", "Ausgang", "Merker"])
        self.type_combo.setCurrentText(var.var_type.capitalize())
        layout.addRow("Typ:", self.type_combo)
        self.value_combo = QComboBox(self)
        self.value_combo.addItems(["0", "1"])
        self.value_combo.setCurrentText("1" if var.value else "0")
        layout.addRow("Wert:", self.value_combo)
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

    def get_values(self):
        name = self.name_edit.text().strip()
        var_type = self.type_combo.currentText()
        value = True if self.value_combo.currentText() == "1" else False
        return name, var_type, value


class VariableAssignmentDialog(QDialog):
    """Dialog zur Zuweisung einer Variable an einen Port."""

    def __init__(self, port, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Variable zuweisen")
        self.setStyleSheet("""
            QLabel { color: white; }
            QComboBox { background-color: #555555; color: white; }
            QPushButton { background-color: #555555; color: white; }
        """)
        self.port = port
        layout = QVBoxLayout(self)
        label = QLabel("Bitte wähle eine Variable für diesen Port aus:")
        layout.addWidget(label)
        self.combo = QComboBox(self)

        # Für Eingänge: "eingang" oder "merker", für Ausgänge: "ausgang" oder "merker"
        if self.port.is_input:
            valid_types = ["eingang", "merker"]
        else:
            valid_types = ["ausgang", "merker"]

        for var in VARIABLES.values():
            if var.var_type in valid_types:
                self.combo.addItem(f"{var.name} ({var.var_type}): {'1' if var.value else '0'}", var.name)
        layout.addWidget(self.combo)

        btn_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK", self)
        self.cancel_button = QPushButton("Abbrechen", self)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_selected_variable(self):
        return self.combo.currentData()


class InputControlDialog(QDialog):
    """Dialog zur Steuerung der Eingangsvariablen (Live-Simulation)."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Eingänge steuern")
        self.setStyleSheet("""
            QPushButton { background-color: #555555; color: white; font-size: 16pt; }
            QLabel { color: white; font-size: 14pt; }
        """)
        self.main_window = main_window
        layout = QVBoxLayout(self)
        self.buttons = {}
        self.refresh_buttons(layout)
        self.setLayout(layout)

        # Positioniere das Fenster unten links
        self.setGeometry(20, self.main_window.height() - 320, 240, 300)

    def refresh_buttons(self, layout):
        for btn in self.buttons.values():
            layout.removeWidget(btn)
            btn.deleteLater()
        self.buttons.clear()

        for var in VARIABLES.values():
            if var.var_type == "eingang":
                btn = QPushButton(f"{var.name}: {'1' if var.value else '0'}")
                btn.clicked.connect(lambda checked, v=var, b=btn: self.toggle_variable(v, b))
                layout.addWidget(btn)
                self.buttons[var.name] = btn

    def toggle_variable(self, var, btn):
        var.value = not var.value
        btn.setText(f"{var.name}: {'1' if var.value else '0'}")
        self.main_window.update_simulation()


# -----------------------------------------------------------------------------
# Variablenpanel
# -----------------------------------------------------------------------------

class VariableListWidget(QListWidget):
    """Liste, die Drag & Drop unterstützt und ein Kontextmenü zum Löschen/Bearbeiten bietet."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setStyleSheet("background-color: #555555; color: white;")

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            mimeData = QMimeData()
            var_name = item.data(Qt.UserRole)
            mimeData.setData("application/x-variable", var_name.encode("utf-8"))
            drag = QDrag(self)
            drag.setMimeData(mimeData)
            drag.exec_(Qt.MoveAction)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if item:
            menu = QMenu(self)
            delete_action = menu.addAction("Löschen")
            edit_action = menu.addAction("Bearbeiten")
            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action == delete_action:
                var_name = item.data(Qt.UserRole)
                if var_name in VARIABLES:
                    del VARIABLES[var_name]
                self.takeItem(self.row(item))
            elif action == edit_action:
                var_name = item.data(Qt.UserRole)
                if var_name in VARIABLES:
                    var = VARIABLES[var_name]
                    dlg = EditVariableDialog(var, self)
                    if dlg.exec_():
                        new_name, new_type, new_value = dlg.get_values()
                        var.name = new_name
                        var.var_type = new_type.lower()
                        var.value = new_value
                        item.setText(f"{new_name} ({new_type}): {'1' if new_value else '0'}")
                        item.setData(Qt.UserRole, new_name)
                        # Ports refreshen:
                        self.parent().parent().update_all_ports()


class VariablePanel(QWidget):
    """Enthält die Liste der Variablen und einen Plus-Button."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.list_widget = VariableListWidget(self)
        layout.addWidget(self.list_widget)
        self.add_button = QPushButton("+", self)
        layout.addWidget(self.add_button)
        self.add_button.clicked.connect(self.add_variable)
        self.init_preset()
        self.setLayout(layout)

    def init_preset(self):
        presets = [
            ("I1", "Eingang", False),
            ("I2", "Eingang", False),
            ("Q1", "Ausgang", False),
            ("Q2", "Ausgang", False),
            ("M1", "Merker", False)
        ]
        for name, var_type, value in presets:
            if name not in VARIABLES:
                VARIABLES[name] = Variable(name, var_type, value)
                text = f"{name} ({var_type}): {'1' if value else '0'}"
                item = QListWidgetItem(text)
                item.setData(Qt.UserRole, name)
                self.list_widget.addItem(item)

    def add_variable(self):
        dialog = NewVariableDialog(self)
        if dialog.exec_():
            name, var_type, value = dialog.get_values()
            if not name or name in VARIABLES:
                return
            VARIABLES[name] = Variable(name, var_type, value)
            text = f"{name} ({var_type}): {'1' if value else '0'}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, name)
            self.list_widget.addItem(item)


# -----------------------------------------------------------------------------
# Gate-, Port- und Wire-Klassen
# -----------------------------------------------------------------------------

class GateItem(QGraphicsRectItem):
    """Repräsentiert ein Logikgatter mit seinen Ports."""

    def __init__(self, gate_type, x, y, width=120, height=90, parent=None):
        super().__init__(0, 0, width, height, parent)
        self.gate_type = gate_type
        self.setBrush(QBrush(QColor(80, 80, 80)))
        self.setPen(QPen(QColor(200, 200, 200), 2))
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        self.setPos(x, y)
        self.input_ports = []
        self.output_ports = []

        if gate_type in ["AND", "OR", "XOR"]:
            self.input_ports.append(PortItem(self, True, QPointF(0, height * 0.3)))
            self.input_ports.append(PortItem(self, True, QPointF(0, height * 0.7)))
            self.output_ports.append(PortItem(self, False, QPointF(width, height / 2)))

        elif gate_type == "SR":
            self.input_ports.append(PortItem(self, True, QPointF(0, height * 0.3), label="S"))
            self.input_ports.append(PortItem(self, True, QPointF(0, height * 0.7), label="R"))
            self.output_ports.append(PortItem(self, False, QPointF(width, height / 2), label="Q"))
            self.memory = False

        elif gate_type == "=":
            self.input_ports.append(PortItem(self, True, QPointF(0, height / 2)))
            self.output_ports.append(PortItem(self, False, QPointF(width, height / 2)))

        elif gate_type == "TON":
            self.input_ports.append(PortItem(self, True, QPointF(0, height * 0.3)))
            self.input_ports.append(PortItem(self, True, QPointF(0, height * 0.7), label="T"))
            self.output_ports.append(PortItem(self, False, QPointF(width, height / 2)))
            self.start_time = None
            self.delay = 1.0

        elif gate_type == "TOF":
            self.input_ports.append(PortItem(self, True, QPointF(0, height * 0.3)))
            self.input_ports.append(PortItem(self, True, QPointF(0, height * 0.7), label="T"))
            self.output_ports.append(PortItem(self, False, QPointF(width, height / 2)))
            self.start_time = None
            self.delay = 1.0

        elif gate_type == "FP":
            self.input_ports.append(PortItem(self, True, QPointF(0, height / 2)))
            self.output_ports.append(PortItem(self, False, QPointF(width, height / 2)))
            self.prev_input = False

        elif gate_type == "FN":
            self.input_ports.append(PortItem(self, True, QPointF(0, height / 2)))
            self.output_ports.append(PortItem(self, False, QPointF(width, height / 2)))
            self.prev_input = True

        self.label = QGraphicsTextItem(gate_type, self)
        self.label.setDefaultTextColor(QColor("white"))
        self.label.setPos(width / 4, height / 4)

    def compute_output(self):
        # Standard: Eingangswert vom ersten Eingang
        result = False
        inp = self.input_ports[0].get_value() if self.input_ports else False

        if self.gate_type == "AND":
            result = self.input_ports[0].get_value() and self.input_ports[1].get_value()

        elif self.gate_type == "OR":
            result = self.input_ports[0].get_value() or self.input_ports[1].get_value()

        elif self.gate_type == "XOR":
            a = self.input_ports[0].get_value()
            b = self.input_ports[1].get_value()
            result = (a and not b) or (not a and b)

        elif self.gate_type == "SR":
            S = self.input_ports[0].get_value()
            R = self.input_ports[1].get_value()
            # Rücksetzdominant
            if R and not S:
                result = False
            elif S and not R:
                result = True
            elif R and S:
                result = False
            else:
                result = self.memory
            self.memory = result

        elif self.gate_type == "=":
            result = self.input_ports[0].get_value()

        elif self.gate_type == "TON":
            control = self.input_ports[0].get_value()
            time_var = self.input_ports[1].variable
            if time_var:
                try:
                    self.delay = float(time_var.name)
                except:
                    pass
            if control:
                if self.start_time is None:
                    self.start_time = time.time()
                if time.time() - self.start_time >= self.delay:
                    result = True
                else:
                    result = False
            else:
                self.start_time = None
                result = False

        elif self.gate_type == "TOF":
            control = self.input_ports[0].get_value()
            time_var = self.input_ports[1].variable
            if time_var:
                try:
                    self.delay = float(time_var.name)
                except:
                    pass
            if not control:
                if self.start_time is None:
                    self.start_time = time.time()
                if time.time() - self.start_time >= self.delay:
                    result = False
                else:
                    result = True
            else:
                self.start_time = None
                result = True

        elif self.gate_type == "FP":
            current = self.input_ports[0].get_value()
            result = current and (not self.prev_input)
            self.prev_input = current

        elif self.gate_type == "FN":
            current = self.input_ports[0].get_value()
            result = (not current) and self.prev_input
            self.prev_input = current

        if result:
            self.setPen(QPen(QColor("lime"), 3))
        else:
            self.setPen(QPen(QColor("red"), 3))

        # Ergebnis an jeden Ausgang weitergeben
        for port in self.output_ports:
            port.set_value(result)


class PortItem(QGraphicsEllipseItem):
    """Repräsentiert einen Anschluss eines Gatters."""

    def __init__(self, parent_gate, is_input=True, relative_pos=QPointF(0, 0), label=""):
        size = 20
        super().__init__(-size/2, -size/2, size, size, parent_gate)
        self.parent_gate = parent_gate
        self.is_input = is_input
        self.relative_pos = relative_pos
        self.setPos(relative_pos)

        self.setBrush(QBrush(QColor("white")))
        self.setPen(QPen(QColor(200, 200, 200), 1))
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        self.setAcceptDrops(True)

        self.variable = None
        self.label = label
        self.negated = False
        self.var_label = None
        self._internal_value = False

        if label:
            self.text = QGraphicsTextItem(label, parent_gate)
            if is_input:
                self.text.setPos(self.x() - 20, self.y() - 10)
            else:
                self.text.setPos(self.x() + 5, self.y() - 10)
        else:
            self.text = None

        self.update_tooltip()

    def get_incoming_wire_value(self):
        scene = self.scene()
        if scene is not None:
            for item in scene.items():
                if isinstance(item, WireItem) and item.dest_port is self:
                    return item.source_port.get_value()
        return None

    def get_value(self):
        incoming = self.get_incoming_wire_value()
        if incoming is not None:
            val = incoming
        else:
            if self.variable is not None:
                val = self.variable.value
            else:
                val = self._internal_value
        return (not val) if self.negated else val

    def set_value(self, value):
        self._internal_value = value
        if self.variable is not None:
            self.variable.value = value
        self.update_color()
        self.update_tooltip()

    def update_tooltip(self):
        if self.variable:
            neg_text = " ¬" if self.negated else ""
            text = f"{self.variable.name}{neg_text} ({self.variable.var_type}): {'1' if self.variable.value else '0'}"
            self.setToolTip(text)
            if not self.var_label:
                self.var_label = QGraphicsTextItem(text, self.parentItem())
            else:
                self.var_label.setPlainText(text)
            if self.negated:
                self.var_label.setDefaultTextColor(QColor("orange"))
            else:
                self.var_label.setDefaultTextColor(QColor("white"))

            if self.is_input:
                x_off = - self.var_label.boundingRect().width() - 5
                self.var_label.setPos(self.x() + x_off, self.y() - 10)
            else:
                self.var_label.setPos(self.x() + 22, self.y() - 10)
        else:
            self.setToolTip("Keine Variable zugewiesen")
            if self.var_label:
                if self.scene():
                    self.scene().removeItem(self.var_label)
                self.var_label = None

    def update_color(self):
        val = self.get_value()
        if (self.get_incoming_wire_value() is None) and (self.variable is None):
            self.setBrush(QBrush(QColor("white")))
            self.setPen(QPen(QColor(200, 200, 200), 1))
        else:
            if val:
                self.setBrush(QBrush(QColor("green")))
                self.setPen(QPen(QColor("lime"), 3))
            else:
                self.setBrush(QBrush(QColor("red")))
                self.setPen(QPen(QColor(200, 200, 200), 1))

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-variable"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-variable"):
            var_data = event.mimeData().data("application/x-variable")
            var_name = str(var_data, "utf-8")
            if var_name in VARIABLES:
                self.variable = VARIABLES[var_name]
                self.update_tooltip()
                self.update_color()
                event.acceptProposedAction()
                return
        event.ignore()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            menu = QMenu()
            action = menu.addAction("Negation umschalten")
            result = menu.exec_(event.screenPos())
            if result == action:
                self.negated = not self.negated
                self.update_tooltip()
                self.update_color()
            event.accept()
            return

        elif event.button() == Qt.LeftButton:
            scene = self.scene()
            if scene.active_connection_source is not None:
                if scene.active_connection_source is self:
                    scene.clear_active_connection()
                else:
                    src = scene.active_connection_source
                    tgt = self
                    if src.parent_gate == tgt.parent_gate:
                        scene.clear_active_connection()
                    elif (src.is_input and not tgt.is_input) or (not src.is_input and tgt.is_input):
                        if src.is_input:
                            source, destination = tgt, src
                        else:
                            source, destination = src, tgt
                        exists = any(
                            isinstance(item, WireItem) and
                            ((item.source_port == source and item.dest_port == destination) or
                             (item.source_port == destination and item.dest_port == source))
                            for item in scene.items()
                        )
                        if not exists:
                            wire = WireItem(source, destination)
                            scene.addItem(wire)
                        scene.clear_active_connection()
                    else:
                        scene.clear_active_connection()
            else:
                scene.active_connection_source = self
                scene.active_connection_line = QGraphicsPathItem()
                dash_pen = QPen(QColor("yellow"), 2, Qt.DashLine)
                scene.active_connection_line.setPen(dash_pen)
                start = self.scenePos()
                path = QPainterPath()
                path.moveTo(start)
                path.lineTo(start)
                scene.active_connection_line.setPath(path)
                scene.addItem(scene.active_connection_line)

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        dialog = VariableAssignmentDialog(self)
        if dialog.exec_():
            var_name = dialog.get_selected_variable()
            if var_name in VARIABLES:
                self.variable = VARIABLES[var_name]
                self.update_tooltip()
                self.update_color()
        super().mouseDoubleClickEvent(event)


class WireItem(QGraphicsPathItem):
    """Verbindet einen Ausgangsport mit einem Eingangsport."""

    def __init__(self, source_port, dest_port, parent=None):
        super().__init__(parent)
        self.source_port = source_port
        self.dest_port = dest_port
        self.setPen(QPen(QColor("blue"), 2))
        self.update_path()

    def update_path(self):
        path = QPainterPath()
        start = self.source_port.scenePos()
        end = self.dest_port.scenePos()
        path.moveTo(start)
        dx = (end.x() - start.x()) / 2
        ctrl1 = QPointF(start.x() + dx, start.y())
        ctrl2 = QPointF(end.x() - dx, end.y())
        path.cubicTo(ctrl1, ctrl2, end)
        self.setPath(path)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            scene = self.scene()
            if scene:
                scene.removeItem(self)
            event.accept()
            return
        super().mousePressEvent(event)

    def paint(self, painter, option, widget):
        self.update_path()
        super().paint(painter, option, widget)


# -----------------------------------------------------------------------------
# Palette
# -----------------------------------------------------------------------------

class PaletteWidget(QListWidget):
    """Liste der verfügbaren Logikbausteine (inkl. neuer Bausteine)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setStyleSheet("background-color: #555555; color: white;")
        for gate in ["AND", "OR", "XOR", "SR", "=", "TON", "TOF", "FP", "FN"]:
            item = QListWidgetItem(gate)
            self.addItem(item)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            mimeData = QMimeData()
            mimeData.setData("application/x-gate", item.text().encode("utf-8"))
            drag = QDrag(self)
            drag.setMimeData(mimeData)
            drag.exec_(Qt.MoveAction)


# -----------------------------------------------------------------------------
# Erweiterte GraphicsScene
# -----------------------------------------------------------------------------

class GraphicsScene(QGraphicsScene):
    """Scene, die Verbindungen verwaltet und neue Gates positioniert."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QColor(53, 53, 53))
        self.active_connection_source = None
        self.active_connection_line = None

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-gate"):
            gate_data = event.mimeData().data("application/x-gate")
            gate_type = str(gate_data, "utf-8")
            pos = event.scenePos()
            new_gate = GateItem(gate_type, pos.x(), pos.y())
            offset = 20
            while any(isinstance(item, GateItem) for item in new_gate.collidingItems()):
                pos += QPointF(offset, offset)
                new_gate.setPos(pos)
            self.addItem(new_gate)
            event.accept()
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if self.active_connection_line and self.active_connection_source:
            start = self.active_connection_source.scenePos()
            path = QPainterPath()
            path.moveTo(start)
            path.lineTo(event.scenePos())
            self.active_connection_line.setPath(path)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        views = self.views()
        if views:
            item = self.itemAt(event.scenePos(), views[0].transform())
        else:
            item = None
        if item is None and self.active_connection_source:
            self.clear_active_connection()
        super().mousePressEvent(event)

    def clear_active_connection(self):
        if self.active_connection_line:
            self.removeItem(self.active_connection_line)
        self.active_connection_source = None
        self.active_connection_line = None


# -----------------------------------------------------------------------------
# Netzwerk-Widget
# -----------------------------------------------------------------------------

class NetworkView(QWidget):
    """Widget für ein Netzwerk (eigene Scene und View)."""

    def __init__(self, network_name, parent=None):
        super().__init__(parent)
        self.network_name = network_name
        layout = QVBoxLayout(self)
        self.header = QWidget(self)
        header_layout = QHBoxLayout(self.header)

        self.label = QLabel(network_name, self.header)
        self.label.setStyleSheet("color: white; font-weight: bold; font-size: 14pt;")
        header_layout.addWidget(self.label)

        self.delete_button = QPushButton("Löschen", self.header)
        self.delete_button.setStyleSheet("background-color: darkred; color: white; font-size: 10pt;")
        header_layout.addWidget(self.delete_button)

        layout.addWidget(self.header)

        self.scene = GraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        # FIX: KEIN setAcceptDrops(True) mehr hier!
        # self.view.setAcceptDrops(True)
        # self.view.viewport().setAcceptDrops(True)

        layout.addWidget(self.view)
        self.scene.setSceneRect(0, 0, 600, 600)
        self.setLayout(layout)


# -----------------------------------------------------------------------------
# Netzwerk-Container
# -----------------------------------------------------------------------------

class NetworkContainer(QWidget):
    """Container, der alle Netzwerke vertikal stapelt."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

    def add_network(self, network_widget):
        self.layout.addWidget(network_widget)

    def remove_network(self, network_widget):
        self.layout.removeWidget(network_widget)
        network_widget.deleteLater()


# -----------------------------------------------------------------------------
# Hauptfenster
# -----------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logikgatter Simulator - FUP (TIA-Stil, Dark Mode)")
        self.resize(1100, 800)

        self.network_container = NetworkContainer(self)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.network_container)
        self.setCentralWidget(self.scroll_area)

        self.add_new_network()  # Erstes Netzwerk

        self.new_network_button = QPushButton("Neues Netzwerk", self)
        self.new_network_button.setStyleSheet("background-color: green; color: white;")
        self.new_network_button.clicked.connect(self.add_new_network)
        self.addToolBar(Qt.TopToolBarArea, self.create_toolbar())

        self.palette = PaletteWidget(self)
        dock_palette = QDockWidget("Palette", self)
        dock_palette.setWidget(self.palette)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_palette)

        self.variable_panel = VariablePanel(self)
        dock_vars = QDockWidget("Variablen", self)
        dock_vars.setWidget(self.variable_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, dock_vars)

        self.sim_button = QPushButton("Simulieren", self)
        self.sim_button.clicked.connect(self.show_simulation_dialog)
        self.statusBar().addPermanentWidget(self.sim_button)

        instr_label = QLabel(
            "Ein Klick: Verbindung starten/abschließen | Doppelklick: Variable zuweisen | Rechtsklick: Negation umschalten | Entf: Löschen"
        )
        instr_label.setStyleSheet("color: lightgray;")
        self.statusBar().addWidget(instr_label)

        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self.update_simulation)
        self.sim_timer.start(200)
        self.simulation_dialog = None

    def create_toolbar(self):
        toolbar = QToolBar("Netzwerksteuerung", self)
        toolbar.addWidget(self.new_network_button)
        return toolbar

    def add_new_network(self):
        network_name = f"Netzwerk {self.network_container.layout.count() + 1}"
        net_view = NetworkView(network_name, self)
        net_view.delete_button.clicked.connect(lambda _, nv=net_view: self.delete_network(nv))
        self.network_container.add_network(net_view)

    def delete_network(self, network_widget):
        self.network_container.remove_network(network_widget)

    def update_all_ports(self):
        for i in range(self.network_container.layout.count()):
            network_widget = self.network_container.layout.itemAt(i).widget()
            scene = network_widget.scene
            for item in scene.items():
                if isinstance(item, PortItem) and item.variable is not None:
                    item.update_tooltip()
                    item.update_color()

    def update_simulation(self):
        for i in range(self.network_container.layout.count()):
            network_widget = self.network_container.layout.itemAt(i).widget()
            scene = network_widget.scene
            for item in scene.items():
                if isinstance(item, GateItem):
                    item.compute_output()
                elif isinstance(item, PortItem):
                    item.update_color()
            scene.update()

    def show_simulation_dialog(self):
        if self.simulation_dialog is None:
            self.simulation_dialog = InputControlDialog(self)
        self.simulation_dialog.show()
        self.simulation_dialog.move(20, self.height() - self.simulation_dialog.height() - 20)
        self.simulation_dialog.raise_()
        self.simulation_dialog.activateWindow()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            for i in range(self.network_container.layout.count()):
                network_widget = self.network_container.layout.itemAt(i).widget()
                scene = network_widget.scene
                for item in list(scene.selectedItems()):
                    scene.removeItem(item)
        else:
            super().keyPressEvent(event)


# -----------------------------------------------------------------------------
# Hauptprogramm
# -----------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QLabel { color: white; }
        QLineEdit { background-color: #555555; color: white; }
        QComboBox { background-color: #555555; color: white; }
        QPushButton { background-color: #555555; color: white; }
        QListWidget { background-color: #555555; color: white; }
    """)
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, QColor(240, 240, 240))
    dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(240, 240, 240))
    dark_palette.setColor(QPalette.ToolTipText, QColor(240, 240, 240))
    dark_palette.setColor(QPalette.Text, QColor(240, 240, 240))
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, QColor(240, 240, 240))
    dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, QColor(35, 35, 35))
    app.setPalette(dark_palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
