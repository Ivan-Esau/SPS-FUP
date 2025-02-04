#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logikgatter Simulator – FUP Lernapplikation im TIA-Stil (Dark Mode)
===========================================================================
Dieses Programm simuliert die Grundlagen der FUP-Programmierung (wie im Siemens TIA Portal)
und bietet:
  • Eine moderne, intuitive Oberfläche im Dark Mode mit einer Zeichenfläche (Canvas) in mehreren Netzwerken,
    die untereinander in einer ScrollArea angezeigt werden.
  • Logikgatter: AND, OR, XOR, SR, RS, =, TON, TOF, FP, FN – per Drag & Drop aus einer Palette.
  • Ein Variablenpanel, das in drei untereinander liegende Fenster gesplittet ist – Eingänge, Ausgänge und Merker.
  • Verbindungen zwischen Elementen:
      – Ein Klick an einem Port startet den Verbindungsmodus (temporäre, gelb gestrichelte Linie).
      – Ein weiterer Klick an einem kompatiblen Zielport verbindet die Elemente.
      – Doppelklick an einem Port öffnet den Zuordnungsdialog (bei Zeit‑Ports öffnet sich ein Dialog zur Eingabe der Zeitkonstante).
      – Rechtsklick an einem Port öffnet ein Kontextmenü zum Umschalten der Negation (zeigt ¬ in Orange).
      – Rechtsklick an einer Verbindung löscht diese.
  • Netzwerke werden vertikal in einer ScrollArea angezeigt, jedes mit Header (Name und Lösch‑Button).
      Neue Gate‑Elemente werden automatisch so positioniert, dass sie nicht zu nahe an anderen liegen.
  • Mit der Entf‑Taste lassen sich ausgewählte Komponenten löschen (bei Ports werden zugewiesene Variablen und Verbindungen entfernt).
  • Die Simulation läuft live (alle 200 ms).
  • Über das Datei‑Menü können Projekte (Variablen) gespeichert und geöffnet werden.
  • Undo/Redo-Funktionalität (Beispielhaft für das Hinzufügen eines Netzwerks).
  • Das SPS‑Dashboard (im unteren Bereich) stellt die SPS‑Ausgänge dar – bei Aktivierung leuchten die entsprechenden Ausgänge.
  • Das SPS‑Dashboard integriert zudem eine direkte Eingangssteuerung, die sich live erweitert, wenn sich die Eingangswerte ändern.

Instruktionen (Statusleiste):
  • Variablen erstellen: Klicke im Variablenpanel auf "+"
  • Variable zuweisen: Doppelklick an einem Port (außer Zeit‑Port) öffnet den Zuordnungsdialog.
  • Für Zeit‑Ports (Label "T"): Doppelklick öffnet einen Dialog zur Eingabe der Zeitkonstante.
  • Verbindung: Ein Klick startet den Verbindungsmodus, ein weiterer klick verbindet.
  • Rechtsklick an einem Port: Umschalten der Negation.
  • Rechtsklick an einer Verbindung: Löscht diese.
  • Mit "Entf" werden ausgewählte Komponenten gelöscht.
  • Neues Netzwerk hinzufügen: Klicke auf "Neues Netzwerk" in der Toolbar.
  • Netzwerk löschen: Über den Lösch‑Button im Header.
  • Projekt speichern/öffnen: Über das Datei‑Menü.
  • Undo/Redo: Über die "Zurück" und "Vor" Buttons.
  • Das SPS‑Dashboard zeigt die Ausgangs‑Variablen als Leuchten (beschriftet korrekt) und integriert die Eingangssteuerung.
"""

# DEBUG-Flag
DEBUG = True

import sys, time, json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsTextItem,
    QVBoxLayout, QWidget, QListWidget, QListWidgetItem, QDockWidget, QDialog,
    QLineEdit, QFormLayout, QPushButton, QLabel, QComboBox, QScrollArea,
    QHBoxLayout, QMenu, QToolBar, QGroupBox, QInputDialog, QGridLayout, QFileDialog, QAction
)
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QDrag, QPalette, QFont
from PyQt5.QtCore import Qt, QPointF, QMimeData, QTimer

# Globales Dictionary für Variablen
VARIABLES = {}

# ----------------------------- Presets ---------------------------------------

def init_presets():
    if DEBUG: print("[DEBUG] init_presets() aufgerufen")
    presets = [
        ("S1", "Eingang", False),
        ("S2", "Eingang", False),
        ("S3", "Eingang", False),
        ("S4", "Eingang", False),
        ("S5", "Eingang", False),
        ("Q1", "Ausgang", False),
        ("Q2", "Ausgang", False),
        ("Q3", "Ausgang", False),
        ("Q4", "Ausgang", False),
        ("Q5", "Ausgang", False),
        ("M1", "Merker", False),
        ("M2", "Merker", False),
        ("M3", "Merker", False),
        ("M4", "Merker", False),
        ("M5", "Merker", False),
        ("M6", "Merker", False),
        ("M7", "Merker", False),
        ("M8", "Merker", False)
    ]
    for name, var_type, value in presets:
        if name not in VARIABLES:
            VARIABLES[name] = Variable(name, var_type, value)
            if DEBUG: print(f"[DEBUG] Preset Variable hinzugefügt: {name}, {var_type}, {value}")

# ----------------------------- Datenstruktur: Variable -----------------------

class Variable:
    """Repräsentiert eine Variable (Eingang, Ausgang, Merker) mit einem binären Wert."""
    def __init__(self, name, var_type, value=False):
        if DEBUG: print(f"[DEBUG] Variable.__init__() - {name}, {var_type}, {value}")
        self.name = name
        self.var_type = var_type.lower()
        self.value = value

# ----------------------------- Dialoge ---------------------------------------

class NewVariableDialog(QDialog):
    """Dialog zur Erstellung einer neuen Variable."""
    def __init__(self, parent=None, default_type=None):
        if DEBUG: print("[DEBUG] NewVariableDialog.__init__() gestartet")
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
        if default_type:
            self.type_combo.setCurrentText(default_type)
            self.type_combo.setEnabled(False)
        layout.addRow("Typ:", self.type_combo)
        self.value_combo = QComboBox(self)
        self.value_combo.addItems(["0", "1"])
        layout.addRow("Wert:", self.value_combo)
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(lambda: print("[DEBUG] NewVariableDialog: OK gedrückt") or self.accept())
        layout.addWidget(self.ok_button)
        self.setLayout(layout)
        if DEBUG: print("[DEBUG] NewVariableDialog.__init__() beendet")
    def get_values(self):
        name = self.name_edit.text().strip()
        var_type = self.type_combo.currentText()
        value = True if self.value_combo.currentText() == "1" else False
        if DEBUG: print(f"[DEBUG] NewVariableDialog.get_values(): {name}, {var_type}, {value}")
        return name, var_type, value

class EditVariableDialog(QDialog):
    """Dialog zur Bearbeitung einer Variable."""
    def __init__(self, var, parent=None):
        if DEBUG: print(f"[DEBUG] EditVariableDialog.__init__() gestartet für Variable: {var.name}")
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
        self.ok_button.clicked.connect(lambda: print(f"[DEBUG] EditVariableDialog: OK gedrückt für {var.name}") or self.accept())
        layout.addWidget(self.ok_button)
        self.setLayout(layout)
        if DEBUG: print(f"[DEBUG] EditVariableDialog.__init__() beendet für Variable: {var.name}")
    def get_values(self):
        name = self.name_edit.text().strip()
        var_type = self.type_combo.currentText()
        value = True if self.value_combo.currentText() == "1" else False
        if DEBUG: print(f"[DEBUG] EditVariableDialog.get_values(): {name}, {var_type}, {value}")
        return name, var_type, value

class VariableAssignmentDialog(QDialog):
    """Dialog zur Zuweisung einer Variable an einen Port."""
    def __init__(self, port, parent=None):
        if DEBUG: print("[DEBUG] VariableAssignmentDialog.__init__() gestartet")
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
        if self.port.is_input:
            valid_types = ["eingang", "ausgang", "merker"]
        else:
            valid_types = ["ausgang", "merker"]
        for var in VARIABLES.values():
            if var.var_type in valid_types:
                self.combo.addItem(f"{var.name} ({var.var_type}): {'1' if var.value else '0'}", var.name)
        layout.addWidget(self.combo)
        btn_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK", self)
        self.cancel_button = QPushButton("Abbrechen", self)
        self.ok_button.clicked.connect(lambda: print("[DEBUG] VariableAssignmentDialog: OK gedrückt") or self.accept())
        self.cancel_button.clicked.connect(lambda: print("[DEBUG] VariableAssignmentDialog: Abbrechen gedrückt") or self.reject())
        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        if DEBUG: print("[DEBUG] VariableAssignmentDialog.__init__() beendet")
    def get_selected_variable(self):
        sel = self.combo.currentData()
        if DEBUG: print(f"[DEBUG] VariableAssignmentDialog.get_selected_variable(): {sel}")
        return sel

class InputControlDialog(QDialog):
    """Dialog zur Steuerung der Eingangsvariablen (Live-Simulation)."""
    def __init__(self, main_window, parent=None):
        if DEBUG: print("[DEBUG] InputControlDialog.__init__() gestartet")
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
        self.setGeometry(20, self.main_window.height() - 320, 240, 300)
        if DEBUG: print("[DEBUG] InputControlDialog.__init__() beendet")
    def refresh_buttons(self, layout):
        if DEBUG: print("[DEBUG] InputControlDialog.refresh_buttons() gestartet")
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
        if DEBUG: print(f"[DEBUG] InputControlDialog.refresh_buttons(): {list(self.buttons.keys())}")
    def toggle_variable(self, var, btn):
        if DEBUG: print(f"[DEBUG] InputControlDialog.toggle_variable() für {var.name}, neuer Wert: {not var.value}")
        var.value = not var.value
        btn.setText(f"{var.name}: {'1' if var.value else '0'}")
        self.main_window.update_simulation()
    def closeEvent(self, event):
        if DEBUG: print("[DEBUG] InputControlDialog.closeEvent() aufgerufen")
        self.main_window.simulation_dialog = None
        event.accept()

# --------------------- Variablenpanel mit Split-Funktionalität ---------------------

class FilteredVariableListWidget(QListWidget):
    """Ein QListWidget, das nur Variablen anzeigt, deren Typ in allowed_types enthalten ist."""
    def __init__(self, allowed_types, parent=None):
        if DEBUG: print("[DEBUG] FilteredVariableListWidget.__init__() gestartet")
        super().__init__(parent)
        self.allowed_types = [t.lower() for t in allowed_types]
        self.setDragEnabled(True)
        self.setStyleSheet("background-color: #555555; color: white;")
        self.refresh()
        if DEBUG: print("[DEBUG] FilteredVariableListWidget.__init__() beendet")
    def refresh(self):
        if DEBUG: print("[DEBUG] FilteredVariableListWidget.refresh() gestartet")
        self.clear()
        for name, var in VARIABLES.items():
            if var.var_type in self.allowed_types:
                text = f"{var.name} ({var.var_type}): {'1' if var.value else '0'}"
                item = QListWidgetItem(text)
                item.setData(Qt.UserRole, name)
                self.addItem(item)
        if DEBUG: print("[DEBUG] FilteredVariableListWidget.refresh() beendet")
    def contextMenuEvent(self, event):
        if DEBUG: print("[DEBUG] FilteredVariableListWidget.contextMenuEvent() gestartet")
        item = self.itemAt(event.pos())
        if item:
            menu = QMenu(self)
            delete_action = menu.addAction("Löschen")
            edit_action = menu.addAction("Bearbeiten")
            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action == delete_action:
                try:
                    var_name = item.data(Qt.UserRole)
                    print(f"[DEBUG] Lösche Variable: {var_name}")
                    if var_name in VARIABLES:
                        del VARIABLES[var_name]
                    self.takeItem(self.row(item))
                except Exception as e:
                    print(f"[DEBUG] Exception in contextMenuEvent Löschen: {e}")
            elif action == edit_action:
                try:
                    old_name = item.data(Qt.UserRole)
                    print(f"[DEBUG] Bearbeite Variable: {old_name}")
                    if old_name in VARIABLES:
                        var = VARIABLES[old_name]
                        dlg = EditVariableDialog(var, self)
                        if dlg.exec_():
                            new_name, new_type, new_value = dlg.get_values()
                            print(f"[DEBUG] Neue Werte: {new_name}, {new_type}, {new_value}")
                            if not new_name:
                                return
                            if new_name != old_name and new_name in VARIABLES:
                                from PyQt5.QtWidgets import QMessageBox
                                QMessageBox.warning(self, "Fehler", f"Die Variable '{new_name}' existiert bereits.")
                                return
                            if new_name != old_name:
                                VARIABLES[new_name] = VARIABLES.pop(old_name)
                            var.name = new_name
                            var.var_type = new_type.lower()
                            var.value = new_value
                            item.setText(f"{new_name} ({new_type}): {'1' if new_value else '0'}")
                            item.setData(Qt.UserRole, new_name)
                            # Verzögert refresh_all aufrufen
                            from PyQt5.QtCore import QTimer
                            QTimer.singleShot(0, self.parent().refresh_all)
                        print("[DEBUG] Bearbeitung abgeschlossen")
                except Exception as e:
                    print(f"[DEBUG] Exception in contextMenuEvent Bearbeiten: {e}")
        else:
            super().contextMenuEvent(event)

class SplitVariablePanel(QWidget):
    """Panel, das drei Bereiche (Eingänge, Ausgänge, Merker) untereinander anzeigt."""
    def __init__(self, parent=None):
        if DEBUG: print("[DEBUG] SplitVariablePanel.__init__() gestartet")
        super().__init__(parent)
        init_presets()
        layout = QVBoxLayout(self)
        self.input_group = QGroupBox("Eingänge")
        self.output_group = QGroupBox("Ausgänge")
        self.merker_group = QGroupBox("Merker")
        self.input_list = FilteredVariableListWidget(["eingang"])
        self.output_list = FilteredVariableListWidget(["ausgang"])
        self.merker_list = FilteredVariableListWidget(["merker"])
        self.input_plus = QPushButton("+")
        self.input_plus.clicked.connect(lambda: self.add_variable("Eingang"))
        self.output_plus = QPushButton("+")
        self.output_plus.clicked.connect(lambda: self.add_variable("Ausgang"))
        self.merker_plus = QPushButton("+")
        self.merker_plus.clicked.connect(lambda: self.add_variable("Merker"))
        in_layout = QVBoxLayout()
        in_layout.addWidget(self.input_list)
        in_layout.addWidget(self.input_plus)
        self.input_group.setLayout(in_layout)
        out_layout = QVBoxLayout()
        out_layout.addWidget(self.output_list)
        out_layout.addWidget(self.output_plus)
        self.output_group.setLayout(out_layout)
        merker_layout = QVBoxLayout()
        merker_layout.addWidget(self.merker_list)
        merker_layout.addWidget(self.merker_plus)
        self.merker_group.setLayout(merker_layout)
        layout.addWidget(self.input_group)
        layout.addWidget(self.output_group)
        layout.addWidget(self.merker_group)
        self.setLayout(layout)
        if DEBUG: print("[DEBUG] SplitVariablePanel.__init__() beendet")
    def add_variable(self, var_type):
        if DEBUG: print(f"[DEBUG] SplitVariablePanel.add_variable() gestartet für Typ: {var_type}")
        dlg = NewVariableDialog(self, default_type=var_type)
        if dlg.exec_():
            name, vtype, value = dlg.get_values()
            print(f"[DEBUG] Neue Variable: {name}, {vtype}, {value}")
            if not name or name in VARIABLES:
                print("[DEBUG] Variable existiert bereits oder kein Name angegeben")
                return
            VARIABLES[name] = Variable(name, vtype, value)
            self.refresh_all()
        if DEBUG: print("[DEBUG] SplitVariablePanel.add_variable() beendet")
    def refresh_all(self):
        if DEBUG: print("[DEBUG] SplitVariablePanel.refresh_all() gestartet")
        self.input_list.refresh()
        self.output_list.refresh()
        self.merker_list.refresh()
        if DEBUG: print("[DEBUG] SplitVariablePanel.refresh_all() beendet")

# --------------------- Dashboard: SPS-Dashboard ---------------------

class LightIndicator(QWidget):
    """Ein Widget, das einen Kreis als 'Leuchte' zeichnet."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._status = False
        self.setMinimumSize(20,20)
        self.setMaximumSize(20,20)
    def setStatus(self, status):
        if DEBUG: print(f"[DEBUG] LightIndicator.setStatus() - {status}")
        self._status = status
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(2,2,-2,-2)
        color = QColor("green") if self._status else QColor("red")
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.black,1))
        painter.drawEllipse(rect)

class SPSDashboard(QWidget):
    """Dashboard, das als SPS-Ausgangsanzeige dient und auch eine dynamische Eingangssteuerung integriert."""
    def __init__(self, parent=None):
        super().__init__(parent)
        if DEBUG: print("[DEBUG] SPSDashboard.__init__() gestartet")
        self.setWindowTitle("SPS Dashboard")
        main_layout = QVBoxLayout(self)
        self.input_group = QGroupBox("Eingänge steuern")
        self.input_layout = QHBoxLayout()
        self.input_buttons = {}
        self.build_input_area()
        self.input_group.setLayout(self.input_layout)
        main_layout.addWidget(self.input_group)
        self.output_group = QGroupBox("SPS Ausgänge")
        self.output_layout = QGridLayout()
        self.output_group.setLayout(self.output_layout)
        self.output_indicators = {}
        self.refresh_output_area()
        main_layout.addWidget(self.output_group)
        self.setLayout(main_layout)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(200)
        if DEBUG: print("[DEBUG] SPSDashboard.__init__() beendet")
    def build_input_area(self):
        if DEBUG: print("[DEBUG] SPSDashboard.build_input_area() gestartet")
        while self.input_layout.count():
            child = self.input_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.input_buttons.clear()
        for name, var in VARIABLES.items():
            if var.var_type == "eingang":
                btn = QPushButton(name)
                btn.setCheckable(True)
                btn.setChecked(var.value)
                btn.clicked.connect(lambda checked, n=name: self.toggle_input(n, checked))
                self.input_layout.addWidget(btn)
                self.input_buttons[name] = btn
        if DEBUG: print(f"[DEBUG] SPSDashboard.build_input_area(): {list(self.input_buttons.keys())}")
    def refresh_output_area(self):
        if DEBUG: print("[DEBUG] SPSDashboard.refresh_output_area() gestartet")
        while self.output_layout.count():
            child = self.output_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.output_indicators.clear()
        row = 0
        for name, var in VARIABLES.items():
            if var.var_type == "ausgang":
                label = QLabel(name)
                label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                indicator = LightIndicator()
                self.output_layout.addWidget(label, row, 0)
                self.output_layout.addWidget(indicator, row, 1)
                self.output_indicators[name] = indicator
                row += 1
        if DEBUG: print("[DEBUG] SPSDashboard.refresh_output_area() beendet")
    def toggle_input(self, name, checked):
        if DEBUG: print(f"[DEBUG] SPSDashboard.toggle_input() - {name}: {checked}")
        if name in VARIABLES:
            VARIABLES[name].value = checked
    def update_dashboard(self):
        # Überprüfe, ob sich die Eingangs- oder Ausgangsvariablen geändert haben
        current_inputs = {name for name, var in VARIABLES.items() if var.var_type == "eingang"}
        if set(self.input_buttons.keys()) != current_inputs:
            if DEBUG: print("[DEBUG] SPSDashboard.update_dashboard(): Eingangsbereich wird neu aufgebaut")
            self.build_input_area()
        for name, btn in self.input_buttons.items():
            if name in VARIABLES:
                btn.setChecked(VARIABLES[name].value)
        current_outputs = {name for name, var in VARIABLES.items() if var.var_type == "ausgang"}
        if set(self.output_indicators.keys()) != current_outputs:
            if DEBUG: print("[DEBUG] SPSDashboard.update_dashboard(): Ausgangsbereich wird neu aufgebaut")
            self.refresh_output_area()
        for name, indicator in self.output_indicators.items():
            if name in VARIABLES:
                indicator.setStatus(VARIABLES[name].value)

# --------------------- GateItem, PortItem, WireItem, PaletteWidget, GraphicsScene ---------------------

class GateItem(QGraphicsRectItem):
    """Repräsentiert ein Logikgatter."""
    def __init__(self, gate_type, x, y, width=120, height=90, parent=None):
        if DEBUG: print(f"[DEBUG] GateItem.__init__() - {gate_type} an Position ({x},{y})")
        super().__init__(0, 0, width, height, parent)
        self.base_width = width
        self.base_height = height
        self.gate_type = gate_type
        self.setBrush(QBrush(QColor(80,80,80)))
        self.setPen(QPen(QColor(200,200,200), 2))
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        self.setPos(x,y)
        self.input_ports = []
        self.output_ports = []
        self.memory = False
        self.start_time = None
        self.delay = 1.0
        self.prev_input = False
        try:
            if gate_type in ["AND", "OR", "XOR"]:
                self.input_ports.append(PortItem(self, True, QPointF(0, self.base_height*0.3)))
                self.input_ports.append(PortItem(self, True, QPointF(0, self.base_height*0.7)))
                self.output_ports.append(PortItem(self, False, QPointF(self.base_width, self.base_height/2)))
            elif gate_type == "SR":
                self.input_ports.append(PortItem(self, True, QPointF(0, self.base_height*0.3), label="S"))
                self.input_ports.append(PortItem(self, True, QPointF(0, self.base_height*0.7), label="R"))
                self.output_ports.append(PortItem(self, False, QPointF(self.base_width, self.base_height/2), label="Q"))
            elif gate_type == "RS":
                self.input_ports.append(PortItem(self, True, QPointF(0, self.base_height*0.3), label="R"))
                self.input_ports.append(PortItem(self, True, QPointF(0, self.base_height*0.7), label="S"))
                self.output_ports.append(PortItem(self, False, QPointF(self.base_width, self.base_height/2), label="Q"))
            elif gate_type == "=":
                self.input_ports.append(PortItem(self, True, QPointF(0, self.base_height/2)))
                self.output_ports.append(PortItem(self, False, QPointF(self.base_width, self.base_height/2)))
            elif gate_type in ["TON", "TOF"]:
                self.input_ports.append(PortItem(self, True, QPointF(0, self.base_height*0.3)))
                self.input_ports.append(PortItem(self, True, QPointF(0, self.base_height*0.7), label="T"))
                self.output_ports.append(PortItem(self, False, QPointF(self.base_width, self.base_height/2)))
            elif gate_type == "FP":
                self.input_ports.append(PortItem(self, True, QPointF(0, self.base_height/2)))
                self.output_ports.append(PortItem(self, False, QPointF(self.base_width, self.base_height/2)))
            elif gate_type == "FN":
                self.input_ports.append(PortItem(self, True, QPointF(0, self.base_height/2)))
                self.output_ports.append(PortItem(self, False, QPointF(self.base_width, self.base_height/2)))
        except Exception as e:
            print(f"[DEBUG] Exception in GateItem.__init__: {e}")
        self.label = QGraphicsTextItem(gate_type, self)
        self.label.setDefaultTextColor(QColor("white"))
        self.label.setPos(self.base_width/4, self.base_height/4)
        self.rearrange_input_ports()
        if DEBUG: print("[DEBUG] GateItem.__init__() beendet")
    def contextMenuEvent(self, event):
        if self.gate_type not in ["AND", "OR", "XOR"]:
            super().contextMenuEvent(event)
            return
        menu = QMenu()
        add_in = menu.addAction("Eingang hinzufügen")
        chosen = menu.exec_(event.screenPos())
        if chosen == add_in:
            self.add_input_port()
            event.accept()
        else:
            event.ignore()
    def add_input_port(self):
        if DEBUG: print("[DEBUG] GateItem.add_input_port() gestartet")
        new_port = PortItem(self, True, QPointF(0,0))
        self.input_ports.append(new_port)
        self.rearrange_input_ports()
        if DEBUG: print("[DEBUG] GateItem.add_input_port() beendet")
    def rearrange_input_ports(self):
        base_height = self.base_height
        extra_height = 30
        count = len(self.input_ports)
        new_height = base_height if count <= 2 else base_height + (count - 2) * extra_height
        self.setRect(0,0,self.base_width,new_height)
        for i, port in enumerate(self.input_ports, start=1):
            frac = i/(count+1.0)
            new_y = new_height * frac
            port.setPos(0, new_y)
        for port in self.output_ports:
            port.setPos(self.base_width, new_height/2)
        self.label.setPos(self.base_width/4, new_height/4)
    def compute_output(self):
        if DEBUG: print(f"[DEBUG] GateItem.compute_output() gestartet für {self.gate_type}")
        result = False
        try:
            if self.gate_type == "AND":
                if not self.input_ports:
                    result = False
                else:
                    result = True
                    for ip in self.input_ports:
                        result = result and ip.get_value()
            elif self.gate_type == "OR":
                result = False
                for ip in self.input_ports:
                    result = result or ip.get_value()
            elif self.gate_type == "XOR":
                accum = False
                for ip in self.input_ports:
                    accum = (accum != ip.get_value())
                result = accum
            elif self.gate_type == "SR":
                S = self.input_ports[0].get_value()
                R = self.input_ports[1].get_value()
                if S and not R:
                    result = True
                elif R and not S:
                    result = False
                elif S and R:
                    result = True
                else:
                    result = self.memory
                self.memory = result
            elif self.gate_type == "RS":
                R = self.input_ports[0].get_value()
                S = self.input_ports[1].get_value()
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
                if self.input_ports:
                    result = self.input_ports[0].get_value()
            elif self.gate_type in ["TON", "TOF"]:
                control = self.input_ports[0].get_value()
                t_port = self.input_ports[1]
                delay_val = None
                if t_port.variable is not None:
                    try:
                        delay_val = float(t_port.variable.name)
                    except ValueError:
                        delay_val = self.delay
                elif hasattr(t_port, "time_value") and t_port.time_value is not None:
                    delay_val = t_port.time_value
                if delay_val is not None:
                    self.delay = delay_val
                if self.gate_type == "TON":
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
                else:
                    if not control:
                        if self.start_time is None:
                            self.start_time = time.time()
                        if (time.time() - self.start_time) >= self.delay:
                            result = False
                        else:
                            result = True
                    else:
                        self.start_time = None
                        result = True
            elif self.gate_type == "FP":
                current = self.input_ports[0].get_value() if self.input_ports else False
                result = current and (not self.prev_input)
                self.prev_input = current
            elif self.gate_type == "FN":
                current = self.input_ports[0].get_value() if self.input_ports else False
                result = (not current) and self.prev_input
                self.prev_input = current
        except Exception as e:
            print(f"[DEBUG] Exception in GateItem.compute_output(): {e}")
        if result:
            self.setPen(QPen(QColor("lime"), 3))
        else:
            self.setPen(QPen(QColor("red"), 3))
        for port in self.output_ports:
            port.set_value(result)
        if DEBUG: print(f"[DEBUG] GateItem.compute_output() beendet: Ergebnis = {result}")

class PortItem(QGraphicsEllipseItem):
    """Repräsentiert einen Anschluss eines Gatters."""
    def __init__(self, parent_gate, is_input=True, relative_pos=QPointF(0,0), label=""):
        size = 20
        super().__init__(-size/2, -size/2, size, size, parent_gate)
        self.parent_gate = parent_gate
        self.is_input = is_input
        self.relative_pos = relative_pos
        self.setPos(relative_pos)
        self.setBrush(QBrush(QColor("white")))
        self.setPen(QPen(QColor(200,200,200),1))
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        self.setAcceptDrops(True)
        self.variable = None
        self.label = label
        self.negated = False
        self.var_label = None
        self._internal_value = False
        self.time_value = None  # Für direkte Zeiteingabe (TON/TOF)
        if label:
            self.text = QGraphicsTextItem(label, parent_gate)
            if is_input:
                self.text.setPos(self.x()-20, self.y()-10)
            else:
                self.text.setPos(self.x()+10, self.y()-10)  # Erhöhter Offset
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
                x_off = - self.var_label.boundingRect().width() - 15
                self.var_label.setPos(self.x()+x_off, self.y()-10)
            else:
                self.var_label.setPos(self.x()+32, self.y()-10)
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
            self.setPen(QPen(QColor(200,200,200),1))
        else:
            if val:
                self.setBrush(QBrush(QColor("green")))
                self.setPen(QPen(QColor("lime"),3))
            else:
                self.setBrush(QBrush(QColor("red")))
                self.setPen(QPen(QColor(200,200,200),1))
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
        if self.label == "T":
            text, ok = QInputDialog.getText(self.scene().views()[0], "Zeit eingeben", "Gib die Zeit in Sekunden ein:")
            if ok:
                try:
                    self.time_value = float(text)
                    self.setToolTip(f"Zeitwert: {self.time_value} s")
                except ValueError:
                    print("[DEBUG] Ungültige Zeiteingabe")
        else:
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
        self.setPen(QPen(QColor("blue"),2))
        self.update_path()
    def update_path(self):
        path = QPainterPath()
        start = self.source_port.scenePos()
        end = self.dest_port.scenePos()
        path.moveTo(start)
        dx = (end.x()-start.x())/2
        ctrl1 = QPointF(start.x()+dx, start.y())
        ctrl2 = QPointF(end.x()-dx, end.y())
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

# --------------------- Palette ---------------------

class PaletteWidget(QListWidget):
    """Liste der verfügbaren Logikgatter."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setStyleSheet("background-color: #555555; color: white;")
        for gate in ["AND", "OR", "XOR", "RS", "SR", "=", "TON", "TOF", "FP", "FN"]:
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

# --------------------- GraphicsScene ---------------------

class GraphicsScene(QGraphicsScene):
    """Scene, die Verbindungen verwaltet und neue Gates positioniert."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QColor(53,53,53))
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
            while any(isinstance(it, GateItem) for it in new_gate.collidingItems()):
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

# --------------------- NetworkView ---------------------

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
        layout.addWidget(self.view)
        self.scene.setSceneRect(0,0,600,600)
        self.setLayout(layout)

# --------------------- NetworkContainer ---------------------

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

# --------------------- Undo/Redo (Beispiel) ---------------------

class Command:
    def undo(self): pass
    def redo(self): pass

class AddGateCommand(Command):
    def __init__(self, scene, gate):
        self.scene = scene
        self.gate = gate
    def undo(self):
        if DEBUG: print("[DEBUG] AddGateCommand.undo()")
        self.scene.removeItem(self.gate)
    def redo(self):
        if DEBUG: print("[DEBUG] AddGateCommand.redo()")
        self.scene.addItem(self.gate)

# --------------------- MainWindow ---------------------

class MainWindow(QMainWindow):
    def __init__(self):
        if DEBUG: print("[DEBUG] MainWindow.__init__() gestartet")
        super().__init__()
        self.setWindowTitle("Logikgatter Simulator - FUP (TIA-Stil, Dark Mode)")
        self.resize(1100,800)
        self.undo_stack = []
        self.redo_stack = []
        self.network_container = NetworkContainer(self)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.network_container)
        self.setCentralWidget(self.scroll_area)
        self.create_menus()
        self.add_new_network()  # Erstes Netzwerk
        self.new_network_button = QPushButton("Neues Netzwerk", self)
        self.new_network_button.setStyleSheet("background-color: green; color: white;")
        self.new_network_button.clicked.connect(self.add_new_network)
        self.undo_button = QPushButton("Zurück", self)
        self.undo_button.clicked.connect(self.undo_action)
        self.redo_button = QPushButton("Vor", self)
        self.redo_button.clicked.connect(self.redo_action)
        toolbar = QToolBar("Netzwerksteuerung", self)
        toolbar.addWidget(self.new_network_button)
        toolbar.addWidget(self.undo_button)
        toolbar.addWidget(self.redo_button)
        self.addToolBar(Qt.TopToolBarArea, toolbar)
        self.palette = PaletteWidget(self)
        dock_palette = QDockWidget("Palette", self)
        dock_palette.setWidget(self.palette)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_palette)
        self.variable_panel = SplitVariablePanel(self)
        dock_vars = QDockWidget("Variablen", self)
        dock_vars.setWidget(self.variable_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, dock_vars)
        self.sim_button = QPushButton("Simulieren", self)
        self.sim_button.clicked.connect(self.show_simulation_dialog)
        self.statusBar().addPermanentWidget(self.sim_button)
        instr_label = QLabel("Ein Klick: Verbindung starten/abschließen | Doppelklick: Variable (oder Zeit eingeben) | Rechtsklick: Negation umschalten | Entf: Löschen")
        instr_label.setStyleSheet("color: lightgray;")
        self.statusBar().addWidget(instr_label)
        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self.update_simulation)
        self.sim_timer.start(200)
        self.simulation_dialog = None
        self.sps_dashboard = SPSDashboard(self)
        dock_dashboard = QDockWidget("SPS Dashboard", self)
        dock_dashboard.setWidget(self.sps_dashboard)
        self.addDockWidget(Qt.BottomDockWidgetArea, dock_dashboard)
        if DEBUG: print("[DEBUG] MainWindow.__init__() beendet")
    def create_menus(self):
        if DEBUG: print("[DEBUG] MainWindow.create_menus() gestartet")
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Datei")
        new_act = QAction("Neu", self)
        new_act.triggered.connect(self.new_project)
        open_act = QAction("Öffnen...", self)
        open_act.triggered.connect(self.open_project)
        save_act = QAction("Speichern...", self)
        save_act.triggered.connect(self.save_project)
        exit_act = QAction("Beenden", self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(new_act)
        file_menu.addAction(open_act)
        file_menu.addAction(save_act)
        file_menu.addSeparator()
        file_menu.addAction(exit_act)
        help_menu = menubar.addMenu("Hilfe")
        help_act = QAction("Hilfe anzeigen", self)
        help_act.triggered.connect(self.show_help)
        help_menu.addAction(help_act)
        if DEBUG: print("[DEBUG] MainWindow.create_menus() beendet")
    def new_project(self):
        if DEBUG: print("[DEBUG] MainWindow.new_project() gestartet")
        global VARIABLES
        for key in list(VARIABLES.keys()):
            del VARIABLES[key]
        init_presets()
        self.variable_panel.refresh_all()
        self.sps_dashboard.refresh_output_area()
        self.update_simulation()
        if DEBUG: print("[DEBUG] MainWindow.new_project() beendet")
    def save_project(self):
        if DEBUG: print("[DEBUG] MainWindow.save_project() gestartet")
        filename, _ = QFileDialog.getSaveFileName(self, "Projekt speichern", "", "JSON Dateien (*.json)")
        if filename:
            data = {
                "variables": {name: {"var_type": var.var_type, "value": var.value} for name, var in VARIABLES.items()},
            }
            try:
                with open(filename, "w") as f:
                    json.dump(data, f, indent=4)
                if DEBUG: print("[DEBUG] Projekt gespeichert")
            except Exception as e:
                print(f"[DEBUG] Exception in save_project: {e}")
        if DEBUG: print("[DEBUG] MainWindow.save_project() beendet")
    def open_project(self):
        if DEBUG: print("[DEBUG] MainWindow.open_project() gestartet")
        filename, _ = QFileDialog.getOpenFileName(self, "Projekt öffnen", "", "JSON Dateien (*.json)")
        if filename:
            try:
                with open(filename, "r") as f:
                    data = json.load(f)
                project_vars = data.get("variables", {})
                for name in list(VARIABLES.keys()):
                    if name in project_vars:
                        VARIABLES[name].var_type = project_vars[name]["var_type"]
                        VARIABLES[name].value = project_vars[name]["value"]
                    else:
                        del VARIABLES[name]
                for name, props in project_vars.items():
                    if name not in VARIABLES:
                        VARIABLES[name] = Variable(name, props["var_type"], props["value"])
                self.variable_panel.refresh_all()
                self.sps_dashboard.refresh_output_area()
                self.update_simulation()
                if DEBUG: print("[DEBUG] Projekt geladen")
            except Exception as e:
                print(f"[DEBUG] Exception in open_project: {e}")
        if DEBUG: print("[DEBUG] MainWindow.open_project() beendet")
    def show_help(self):
        if DEBUG: print("[DEBUG] MainWindow.show_help() gestartet")
        dlg = QDialog(self)
        dlg.setWindowTitle("Hilfe")
        dlg.setMinimumSize(600,400)
        layout = QVBoxLayout(dlg)
        help_text = (
            "<h2>Willkommen im FUP-Simulator</h2>"
            "<p>Dieses Programm simuliert die SPS-Programmierung im TIA-Stil.</p>"
            "<h3>Bedienung:</h3>"
            "<ul>"
            "<li>Variablen erstellen: Klicke im Variablenpanel auf '+'.</li>"
            "<li>Variable zuweisen: Doppelklick an einem Port (außer Zeit‑Port) öffnet den Zuordnungsdialog.</li>"
            "<li>Zeit‑Ports (Label 'T'): Doppelklick öffnet einen Dialog zur Eingabe der Zeitkonstante.</li>"
            "<li>Verbindung: Ein Klick startet den Verbindungsmodus, ein weiterer klick verbindet.</li>"
            "<li>Negation umschalten: Rechtsklick an einem Port.</li>"
            "<li>Elemente entfernen: Markiere ein Element und drücke 'Entf'.</li>"
            "<li>Neue Netzwerke hinzufügen: Button in der Toolbar.</li>"
            "<li>Projekt speichern/öffnen: Über das Datei-Menü.</li>"
            "<li>Undo/Redo: Nutze die 'Zurück' und 'Vor' Buttons.</li>"
            "<li>SPS Dashboard: Steuere Eingänge direkt und beobachte die Ausgänge als Leuchten.</li>"
            "</ul>"
        )
        label = QLabel(help_text)
        label.setWordWrap(True)
        layout.addWidget(label)
        dlg.setLayout(layout)
        dlg.exec_()
        if DEBUG: print("[DEBUG] MainWindow.show_help() beendet")
    def add_new_network(self):
        if DEBUG: print("[DEBUG] MainWindow.add_new_network() gestartet")
        network_name = f"Netzwerk {self.network_container.layout.count()+1}"
        net_view = NetworkView(network_name, self)
        net_view.delete_button.clicked.connect(lambda _, nv=net_view: self.delete_network(nv))
        self.network_container.add_network(net_view)
        self.undo_stack.append(AddGateCommand(net_view.scene, net_view))
        self.redo_stack.clear()
        if DEBUG: print("[DEBUG] MainWindow.add_new_network() beendet")
    def delete_network(self, network_widget):
        if DEBUG: print("[DEBUG] MainWindow.delete_network() gestartet")
        self.network_container.remove_network(network_widget)
        if DEBUG: print("[DEBUG] MainWindow.delete_network() beendet")
    def update_all_ports(self):
        if DEBUG: print("[DEBUG] MainWindow.update_all_ports() gestartet")
        for i in range(self.network_container.layout.count()):
            network_widget = self.network_container.layout.itemAt(i).widget()
            scene = network_widget.scene
            for item in scene.items():
                if isinstance(item, PortItem):
                    item.update_tooltip()
                    item.update_color()
        if DEBUG: print("[DEBUG] MainWindow.update_all_ports() beendet")
    def update_simulation(self):
        if DEBUG: print("[DEBUG] MainWindow.update_simulation() gestartet")
        for i in range(self.network_container.layout.count()):
            network_widget = self.network_container.layout.itemAt(i).widget()
            scene = network_widget.scene
            for item in scene.items():
                if isinstance(item, GateItem):
                    item.compute_output()
                elif isinstance(item, PortItem):
                    item.update_color()
            scene.update()
        self.sps_dashboard.update_dashboard()
        if DEBUG: print("[DEBUG] MainWindow.update_simulation() beendet")
    def show_simulation_dialog(self):
        if DEBUG: print("[DEBUG] MainWindow.show_simulation_dialog() gestartet")
        self.sps_dashboard.show()
        self.sps_dashboard.raise_()
        self.sps_dashboard.activateWindow()
        if DEBUG: print("[DEBUG] MainWindow.show_simulation_dialog() beendet")
    def undo_action(self):
        if self.undo_stack:
            cmd = self.undo_stack.pop()
            cmd.undo()
            self.redo_stack.append(cmd)
    def redo_action(self):
        if self.redo_stack:
            cmd = self.redo_stack.pop()
            cmd.redo()
            self.undo_stack.append(cmd)
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            for i in range(self.network_container.layout.count()):
                network_widget = self.network_container.layout.itemAt(i).widget()
                scene = network_widget.scene
                for item in list(scene.selectedItems()):
                    if isinstance(item, WireItem):
                        scene.removeItem(item)
                    elif isinstance(item, PortItem):
                        for wire in list(scene.items()):
                            if isinstance(wire, WireItem) and (wire.source_port == item or wire.dest_port == item):
                                scene.removeItem(wire)
                        item.variable = None
                        item.update_tooltip()
                        item.update_color()
                    else:
                        scene.removeItem(item)
        else:
            super().keyPressEvent(event)
    def closeEvent(self, event):
        if DEBUG: print("[DEBUG] MainWindow.closeEvent() aufgerufen")
        event.accept()

# --------------------- Hauptprogramm ---------------------

def main():
    if DEBUG: print("[DEBUG] main() gestartet")
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QLabel { color: white; }
        QLineEdit { background-color: #555555; color: white; }
        QComboBox { background-color: #555555; color: white; }
        QPushButton { background-color: #555555; color: white; }
        QListWidget { background-color: #555555; color: white; }
    """)
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53,53,53))
    dark_palette.setColor(QPalette.WindowText, QColor(240,240,240))
    dark_palette.setColor(QPalette.Base, QColor(35,35,35))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53,53,53))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(240,240,240))
    dark_palette.setColor(QPalette.ToolTipText, QColor(240,240,240))
    dark_palette.setColor(QPalette.Text, QColor(240,240,240))
    dark_palette.setColor(QPalette.Button, QColor(53,53,53))
    dark_palette.setColor(QPalette.ButtonText, QColor(240,240,240))
    dark_palette.setColor(QPalette.BrightText, QColor(255,0,0))
    dark_palette.setColor(QPalette.Link, QColor(42,130,218))
    dark_palette.setColor(QPalette.Highlight, QColor(42,130,218))
    dark_palette.setColor(QPalette.HighlightedText, QColor(35,35,35))
    app.setPalette(dark_palette)
    window = MainWindow()
    window.show()
    if DEBUG: print("[DEBUG] main() beendet – Starte Event Loop")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
