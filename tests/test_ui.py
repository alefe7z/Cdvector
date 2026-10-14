"""GUI integration exercised on the Windows CI runner (skipped without a display)."""
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from cdvector.app import Editor
import tkinter as tk

@unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'), 'No graphical display')
class UITests(unittest.TestCase):
    def setUp(self):
        self.root=tk.Tk();self.editor=Editor(self.root);self.root.update()
    def tearDown(self):self.root.destroy()
    def event(self,x,y):
        x,y=self.editor.screen((x,y));return SimpleNamespace(x=x,y=y)
    def test_draw_move_nodes_undo_save_export(self):
        e=self.editor;e.choose('rect')
        e.down(self.event(10,20));e.motion(self.event(110,120));e.up(self.event(110,120))
        self.assertEqual(len(e.doc.shapes),1)
        e.choose('nodes');e.down(self.event(10,20));e.motion(self.event(30,40));e.up(self.event(30,40))
        self.assertAlmostEqual(e.doc.shapes[0].points[0][0],30)
        e.undo();self.assertAlmostEqual(e.doc.shapes[0].points[0][0],10)
        e.redo();self.assertAlmostEqual(e.doc.shapes[0].points[0][0],30)
        e.choose('bezier')
        for p in [(10,10),(50,100),(100,50),(150,150)]:e.down(self.event(*p))
        self.assertEqual(e.doc.shapes[-1].kind,'bezier')
        with tempfile.TemporaryDirectory() as tmp:
            project=Path(tmp)/'test.cdvector';svg=Path(tmp)/'test.svg'
            with patch('cdvector.app.filedialog.asksaveasfilename',return_value=str(project)):self.assertTrue(e.save())
            with patch('cdvector.app.filedialog.asksaveasfilename',return_value=str(svg)):e.export()
            self.assertIn('<path',svg.read_text())
            e.new()
            with patch('cdvector.app.filedialog.askopenfilename',return_value=str(project)):e.open()
            self.assertEqual(len(e.doc.shapes),2)
